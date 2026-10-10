import json
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from issues.models import ReporterModel, IssueModel


class Command(BaseCommand):
    help = 'Load reporters and issues from JSON fixtures into the PostgreSQL database'

    def handle(self, *args, **options):
        reporters_file = settings.BASE_DIR / 'reporters.json'
        issues_file = settings.BASE_DIR / 'issues.json'

        reporters_count = 0
        if reporters_file.exists():
            with open(reporters_file, 'r', encoding='utf-8') as f:
                reporters = json.load(f)
                for item in reporters:
                    ReporterModel.objects.update_or_create(
                        id=int(item['id']),
                        defaults={
                            'name': item.get('name', ''),
                            'email': item.get('email', ''),
                            'team': item.get('team', ''),
                        }
                    )
                    reporters_count += 1
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {reporters_count} reporters.'))
        else:
            self.stdout.write(self.style.WARNING(f'File not found: {reporters_file}'))

        issues_count = 0
        if issues_file.exists():
            with open(issues_file, 'r', encoding='utf-8') as f:
                issues = json.load(f)
                for item in issues:
                    IssueModel.objects.update_or_create(
                        id=int(item['id']),
                        defaults={
                            'title': item.get('title', ''),
                            'description': item.get('description', ''),
                            'status': item.get('status', 'open'),
                            'priority': item.get('priority', 'medium'),
                            'reporter_id': int(item.get('reporter_id', 0)),
                            'created_at': str(item.get('created_at', '')),
                            'message': item.get('message', ''),
                        }
                    )
                    issues_count += 1
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {issues_count} issues.'))
        else:
            self.stdout.write(self.style.WARNING(f'File not found: {issues_file}'))
