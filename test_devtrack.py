import os
import sys
import json
import django
from django.test import Client

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devtrack.settings')
django.setup()

from issues.models import BaseEntity, Reporter, Issue, CriticalIssue, LowPriorityIssue


def test_oop_models():
    print("--- Running OOP Models Tests ---")
    
    # Reporter test
    r = Reporter(id=1, name="Alice", email="alice@test.com", team="backend")
    r.validate()
    assert r.to_dict() == {"id": 1, "name": "Alice", "email": "alice@test.com", "team": "backend"}
    print("✓ Reporter instantiation and validation passed")
    
    # Invalid Reporter test
    r_invalid = Reporter(id=2, name="", email="invalid_email", team="frontend")
    try:
        r_invalid.validate()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Name cannot be empty" in str(e)
        print("✓ Reporter validation error check passed")

    # Issue polymorphic describe() test
    critical = CriticalIssue(id=1, title="Crash on startup", description="App crashes", status="open", priority="critical", reporter_id=1)
    critical.validate()
    assert critical.describe() == "[URGENT] Crash on startup — needs immediate attention"
    print("✓ CriticalIssue describe() passed")

    low = LowPriorityIssue(id=2, title="Dark mode theme tweak", description="Change hex color", status="open", priority="low", reporter_id=1)
    low.validate()
    assert low.describe() == "Dark mode theme tweak — low priority, handle when free"
    print("✓ LowPriorityIssue describe() passed")

    medium = Issue(id=3, title="Update docs", description="API docs update", status="open", priority="medium", reporter_id=1)
    medium.validate()
    assert medium.describe() == "Update docs [medium]"
    print("✓ Base Issue describe() passed")


def test_api_endpoints():
    print("\n--- Running API Endpoint Integration Tests ---")
    client = Client()

    # Reset test database
    from issues.models import ReporterModel, IssueModel
    ReporterModel.objects.all().delete()
    IssueModel.objects.all().delete()

    # 1. POST /api/reporters/ - Success
    resp = client.post(
        '/api/reporters/',
        data=json.dumps({"id": 1, "name": "Jane Doe", "email": "jane@devtrack.org", "team": "backend"}),
        content_type='application/json'
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.content}"
    data = resp.json()
    assert data["id"] == 1
    assert data["name"] == "Jane Doe"
    print("✓ POST /api/reporters/ (201 Created) passed")

    # 2. POST /api/reporters/ - Validation Failure
    resp = client.post(
        '/api/reporters/',
        data=json.dumps({"id": 2, "name": "Bob", "email": "bad_email_no_at", "team": "devops"}),
        content_type='application/json'
    )
    assert resp.status_code == 400
    assert "Invalid email" in resp.json()["error"]
    print("✓ POST /api/reporters/ (400 Bad Request) passed")

    # 3. GET /api/reporters/ - Get all
    resp = client.get('/api/reporters/')
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    print("✓ GET /api/reporters/ (All) passed")

    # 4. GET /api/reporters/?id=1 - Get single
    resp = client.get('/api/reporters/?id=1')
    assert resp.status_code == 200
    assert resp.json()["name"] == "Jane Doe"
    print("✓ GET /api/reporters/?id=1 (200 OK) passed")

    # 5. GET /api/reporters/?id=99 - Not found
    resp = client.get('/api/reporters/?id=99')
    assert resp.status_code == 404
    assert resp.json()["error"] == "Reporter not found"
    print("✓ GET /api/reporters/?id=99 (404 Not Found) passed")

    # 6. POST /api/issues/ - Critical Issue Success
    resp = client.post(
        '/api/issues/',
        data=json.dumps({
            "id": 1,
            "title": "Login button not working on mobile",
            "description": "Users on iOS 17 cannot tap the login button",
            "status": "open",
            "priority": "critical",
            "reporter_id": 1
        }),
        content_type='application/json'
    )
    assert resp.status_code == 201
    issue_data = resp.json()
    assert issue_data["message"] == "[URGENT] Login button not working on mobile — needs immediate attention"
    print("✓ POST /api/issues/ Critical (201 Created) passed")

    # 7. POST /api/issues/ - Low Priority Issue Success
    resp = client.post(
        '/api/issues/',
        data=json.dumps({
            "id": 2,
            "title": "Update button spacing",
            "description": "Adjust padding by 2px",
            "status": "open",
            "priority": "low",
            "reporter_id": 1
        }),
        content_type='application/json'
    )
    assert resp.status_code == 201
    assert resp.json()["message"] == "Update button spacing — low priority, handle when free"
    print("✓ POST /api/issues/ Low Priority (201 Created) passed")

    # 8. POST /api/issues/ - Validation Failure (empty title)
    resp = client.post(
        '/api/issues/',
        data=json.dumps({
            "id": 3,
            "title": "",
            "description": "Missing title test",
            "status": "open",
            "priority": "medium",
            "reporter_id": 1
        }),
        content_type='application/json'
    )
    assert resp.status_code == 400
    assert "Title cannot be empty" in resp.json()["error"]
    print("✓ POST /api/issues/ (400 Empty Title) passed")

    # 9. GET /api/issues/ - Get all
    resp = client.get('/api/issues/')
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    print("✓ GET /api/issues/ (All) passed")

    # 10. GET /api/issues/?id=1 - Get single issue
    resp = client.get('/api/issues/?id=1')
    assert resp.status_code == 200
    assert resp.json()["title"] == "Login button not working on mobile"
    print("✓ GET /api/issues/?id=1 (200 OK) passed")

    # 11. GET /api/issues/?id=999 - Issue Not Found
    resp = client.get('/api/issues/?id=999')
    assert resp.status_code == 404
    assert resp.json()["error"] == "Issue not found"
    print("✓ GET /api/issues/?id=999 (404 Not Found) passed")

    # 12. GET /api/issues/?status=open - Filter by status
    resp = client.get('/api/issues/?status=open')
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    print("✓ GET /api/issues/?status=open (Filtered) passed")


def test_database_persistence():
    print("\n--- Running Database Persistence Tests ---")
    from django.db import connection
    from issues.models import ReporterModel, IssueModel

    connection.ensure_connection()
    engine = connection.settings_dict['ENGINE']
    print(f"✓ Connected to database using engine: {engine}")

    # Clean test state
    ReporterModel.objects.filter(id__gte=100).delete()
    IssueModel.objects.filter(id__gte=100).delete()

    # Create and verify ReporterModel
    r = ReporterModel.objects.create(id=101, name="Test Dev", email="dev@test.org", team="infra")
    assert ReporterModel.objects.filter(id=101).exists()
    assert str(r) == "Test Dev (infra)"
    print("✓ ReporterModel ORM persistence and __str__ passed")

    # Create and verify IssueModel
    IssueModel.objects.create(
        id=201,
        title="DB connection pool saturation",
        description="Pool max size reached",
        status="open",
        priority="critical",
        reporter_id=101,
        created_at="2026-10-10",
        message="[URGENT] DB connection pool saturation — needs immediate attention"
    )
    assert IssueModel.objects.filter(id=201).exists()
    assert IssueModel.objects.filter(id=201, priority="critical").count() == 1
    print("✓ IssueModel ORM persistence and filtering passed")

    # Clean up test records
    ReporterModel.objects.filter(id=101).delete()
    IssueModel.objects.filter(id=201).delete()


if __name__ == '__main__':
    test_oop_models()
    test_database_persistence()
    test_api_endpoints()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉")
