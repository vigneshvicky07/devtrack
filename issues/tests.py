import json
from django.test import TestCase, Client
from django.core.management import call_command
from django.db import connection
from django.conf import settings
from issues.models import (
    BaseEntity,
    Reporter,
    Issue,
    CriticalIssue,
    LowPriorityIssue,
    ReporterModel,
    IssueModel,
)


class DatabaseConfigurationTestCase(TestCase):
    """Validates active database connection and engine."""

    def test_database_connection(self):
        connection.ensure_connection()
        self.assertTrue(connection.is_usable())
        engine = settings.DATABASES['default']['ENGINE']
        self.assertIn(engine, [
            'django.db.backends.postgresql',
            'django.db.backends.sqlite3',
        ])


class OOPDomainModelsTestCase(TestCase):
    """Validates domain models, polymorphism, and validation logic."""

    def test_reporter_valid_and_to_dict(self):
        reporter = Reporter(id=1, name="Alice", email="alice@test.com", team="backend")
        reporter.validate()
        data = reporter.to_dict()
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['name'], "Alice")
        self.assertEqual(data['email'], "alice@test.com")
        self.assertEqual(data['team'], "backend")

    def test_reporter_empty_name_raises_value_error(self):
        reporter = Reporter(id=2, name="", email="bob@test.com", team="frontend")
        with self.assertRaises(ValueError) as ctx:
            reporter.validate()
        self.assertIn("Name cannot be empty", str(ctx.exception))

    def test_reporter_invalid_email_raises_value_error(self):
        reporter = Reporter(id=3, name="Charlie", email="no_at_symbol_email", team="qa")
        with self.assertRaises(ValueError) as ctx:
            reporter.validate()
        self.assertIn("Invalid email", str(ctx.exception))

    def test_issue_valid_and_to_dict(self):
        issue = Issue(
            id=1,
            title="Database slow query",
            description="Query takes 5 seconds",
            status="open",
            priority="high",
            reporter_id=1
        )
        issue.validate()
        data = issue.to_dict()
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['title'], "Database slow query")
        self.assertEqual(data['status'], "open")
        self.assertEqual(data['priority'], "high")

    def test_issue_empty_title_raises_value_error(self):
        issue = Issue(id=2, title="", description="desc", status="open", priority="low", reporter_id=1)
        with self.assertRaises(ValueError) as ctx:
            issue.validate()
        self.assertIn("Title cannot be empty", str(ctx.exception))

    def test_issue_invalid_status_raises_value_error(self):
        issue = Issue(id=3, title="Bug", description="desc", status="unknown_status", priority="low", reporter_id=1)
        with self.assertRaises(ValueError) as ctx:
            issue.validate()
        self.assertIn("Invalid status", str(ctx.exception))

    def test_issue_invalid_priority_raises_value_error(self):
        issue = Issue(id=4, title="Bug", description="desc", status="open", priority="ultra_high", reporter_id=1)
        with self.assertRaises(ValueError) as ctx:
            issue.validate()
        self.assertIn("Invalid priority", str(ctx.exception))

    def test_polymorphic_describe_critical_issue(self):
        issue = CriticalIssue(
            id=5,
            title="Payment gateway failure",
            description="Stripe checkout broken",
            status="open",
            priority="critical",
            reporter_id=1
        )
        issue.validate()
        self.assertEqual(issue.describe(), "[URGENT] Payment gateway failure — needs immediate attention")

    def test_polymorphic_describe_low_priority_issue(self):
        issue = LowPriorityIssue(
            id=6,
            title="Adjust navbar footer margin",
            description="Padding 5px",
            status="open",
            priority="low",
            reporter_id=1
        )
        issue.validate()
        self.assertEqual(issue.describe(), "Adjust navbar footer margin — low priority, handle when free")

    def test_describe_base_issue(self):
        issue = Issue(
            id=7,
            title="Refactor auth service",
            description="Clean code",
            status="in_progress",
            priority="medium",
            reporter_id=1
        )
        issue.validate()
        self.assertEqual(issue.describe(), "Refactor auth service [medium]")


class ORMDatabaseModelsTestCase(TestCase):
    """Validates Django ORM models and database persistence."""

    def setUp(self):
        ReporterModel.objects.all().delete()
        IssueModel.objects.all().delete()

    def test_reporter_model_crud(self):
        reporter = ReporterModel.objects.create(
            id=10,
            name="Diana",
            email="diana@devtrack.org",
            team="infra"
        )
        self.assertEqual(str(reporter), "Diana (infra)")
        self.assertEqual(reporter.to_dict()['email'], "diana@devtrack.org")

        # Update
        reporter.team = "security"
        reporter.save()
        updated = ReporterModel.objects.get(id=10)
        self.assertEqual(updated.team, "security")

    def test_issue_model_crud_and_filtering(self):
        issue = IssueModel.objects.create(
            id=20,
            title="Redis memory leak",
            description="Redis cache filling up",
            status="open",
            priority="critical",
            reporter_id=10,
            created_at="2026-10-10 12:00:00",
            message="[URGENT] Redis memory leak — needs immediate attention"
        )
        self.assertEqual(str(issue), "Redis memory leak [critical]")
        self.assertEqual(issue.to_dict()['message'], "[URGENT] Redis memory leak — needs immediate attention")

        # Create another issue
        IssueModel.objects.create(
            id=21,
            title="Fix typo in docs",
            description="Spelling error in readme",
            status="closed",
            priority="low",
            reporter_id=10,
            created_at="2026-10-10 12:05:00"
        )

        open_issues = IssueModel.objects.filter(status="open")
        self.assertEqual(open_issues.count(), 1)
        self.assertEqual(open_issues.first().id, 20)


class ReporterAPIEndpointsTestCase(TestCase):
    """Integration tests for /api/reporters/ HTTP endpoints."""

    def setUp(self):
        self.client = Client()
        ReporterModel.objects.all().delete()
        IssueModel.objects.all().delete()

    def test_create_reporter_success(self):
        payload = {
            "id": 1,
            "name": "Jane Doe",
            "email": "jane@devtrack.org",
            "team": "backend"
        }
        resp = self.client.post('/api/reporters/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['name'], "Jane Doe")
        self.assertTrue(ReporterModel.objects.filter(id=1).exists())

    def test_create_reporter_update_existing_id(self):
        payload1 = {"id": 1, "name": "Jane", "email": "jane@test.org", "team": "dev"}
        self.client.post('/api/reporters/', data=json.dumps(payload1), content_type='application/json')

        # Update with same id
        payload2 = {"id": 1, "name": "Jane Doe", "email": "jane.doe@test.org", "team": "lead"}
        resp = self.client.post('/api/reporters/', data=json.dumps(payload2), content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(ReporterModel.objects.count(), 1)
        record = ReporterModel.objects.get(id=1)
        self.assertEqual(record.name, "Jane Doe")
        self.assertEqual(record.team, "lead")

    def test_create_reporter_missing_field(self):
        payload = {"id": 2, "name": "Bob", "email": "bob@devtrack.org"}  # missing team
        resp = self.client.post('/api/reporters/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Missing required field", resp.json()['error'])

    def test_create_reporter_invalid_email(self):
        payload = {"id": 3, "name": "Bob", "email": "invalid_email_format", "team": "devops"}
        resp = self.client.post('/api/reporters/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid email", resp.json()['error'])

    def test_create_reporter_invalid_json(self):
        resp = self.client.post('/api/reporters/', data="not-a-json", content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], "Invalid JSON format")

    def test_get_all_reporters(self):
        ReporterModel.objects.create(id=1, name="Alice", email="alice@test.com", team="core")
        ReporterModel.objects.create(id=2, name="Bob", email="bob@test.com", team="mobile")
        resp = self.client.get('/api/reporters/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 2)

    def test_get_reporter_by_id_success(self):
        ReporterModel.objects.create(id=1, name="Alice", email="alice@test.com", team="core")
        resp = self.client.get('/api/reporters/?id=1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['name'], "Alice")

    def test_get_reporter_by_id_not_found(self):
        resp = self.client.get('/api/reporters/?id=999')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()['error'], "Reporter not found")

    def test_get_reporter_invalid_id_param(self):
        resp = self.client.get('/api/reporters/?id=invalid_id')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], "Invalid id parameter")

    def test_reporter_method_not_allowed(self):
        resp = self.client.delete('/api/reporters/')
        self.assertEqual(resp.status_code, 405)


class IssueAPIEndpointsTestCase(TestCase):
    """Integration tests for /api/issues/ HTTP endpoints."""

    def setUp(self):
        self.client = Client()
        ReporterModel.objects.all().delete()
        IssueModel.objects.all().delete()
        ReporterModel.objects.create(id=1, name="Alice", email="alice@test.com", team="core")

    def test_create_critical_issue_success(self):
        payload = {
            "id": 1,
            "title": "Production database connection spike",
            "description": "Max connections reached on primary instance",
            "status": "open",
            "priority": "critical",
            "reporter_id": 1
        }
        resp = self.client.post('/api/issues/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['message'], "[URGENT] Production database connection spike — needs immediate attention")
        self.assertTrue(IssueModel.objects.filter(id=1, priority="critical").exists())

    def test_create_low_priority_issue_success(self):
        payload = {
            "id": 2,
            "title": "Minor styling alignment on footer",
            "description": "Shift by 4px to the right",
            "status": "open",
            "priority": "low",
            "reporter_id": 1
        }
        resp = self.client.post('/api/issues/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['message'], "Minor styling alignment on footer — low priority, handle when free")

    def test_create_medium_issue_success(self):
        payload = {
            "id": 3,
            "title": "Add audit logging for profile edits",
            "description": "Log timestamp and IP",
            "status": "open",
            "priority": "medium",
            "reporter_id": 1
        }
        resp = self.client.post('/api/issues/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['message'], "Add audit logging for profile edits [medium]")

    def test_create_issue_missing_title(self):
        payload = {
            "id": 4,
            "title": "",
            "description": "Missing title",
            "status": "open",
            "priority": "low",
            "reporter_id": 1
        }
        resp = self.client.post('/api/issues/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Title cannot be empty", resp.json()['error'])

    def test_create_issue_invalid_status(self):
        payload = {
            "id": 5,
            "title": "Invalid status test",
            "description": "desc",
            "status": "invalid_status",
            "priority": "low",
            "reporter_id": 1
        }
        resp = self.client.post('/api/issues/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid status", resp.json()['error'])

    def test_get_all_issues(self):
        IssueModel.objects.create(id=1, title="Issue 1", description="d1", status="open", priority="high", reporter_id=1, created_at="2026-10-10")
        IssueModel.objects.create(id=2, title="Issue 2", description="d2", status="closed", priority="low", reporter_id=1, created_at="2026-10-10")
        resp = self.client.get('/api/issues/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_get_issue_by_id(self):
        IssueModel.objects.create(id=1, title="Login bug", description="d1", status="open", priority="high", reporter_id=1, created_at="2026-10-10")
        resp = self.client.get('/api/issues/?id=1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['title'], "Login bug")

    def test_get_issue_by_id_not_found(self):
        resp = self.client.get('/api/issues/?id=999')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()['error'], "Issue not found")

    def test_get_issues_filter_by_status(self):
        IssueModel.objects.create(id=1, title="Open issue", description="d1", status="open", priority="high", reporter_id=1, created_at="2026-10-10")
        IssueModel.objects.create(id=2, title="Closed issue", description="d2", status="closed", priority="low", reporter_id=1, created_at="2026-10-10")
        resp = self.client.get('/api/issues/?status=open')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], "Open issue")


class ManagementCommandTestCase(TestCase):
    """Validates the load_json_data management command."""

    def setUp(self):
        ReporterModel.objects.all().delete()
        IssueModel.objects.all().delete()

    def test_load_json_data_execution(self):
        call_command('load_json_data')
        self.assertGreaterEqual(ReporterModel.objects.count(), 1)
        self.assertGreaterEqual(IssueModel.objects.count(), 1)
