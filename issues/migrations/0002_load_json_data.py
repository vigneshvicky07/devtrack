import json
from pathlib import Path
from django.db import migrations


def load_initial_json_data(apps, schema_editor):
    ReporterModel = apps.get_model('issues', 'ReporterModel')
    IssueModel = apps.get_model('issues', 'IssueModel')
    base_dir = Path(__file__).resolve().parent.parent.parent

    reporters_file = base_dir / 'reporters.json'
    if reporters_file.exists():
        try:
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
        except Exception:
            pass

    issues_file = base_dir / 'issues.json'
    if issues_file.exists():
        try:
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
        except Exception:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_json_data, reverse_code=migrations.RunPython.noop),
    ]
