import json
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from issues.models import Reporter, Issue, CriticalIssue, LowPriorityIssue

REPORTERS_FILE = settings.BASE_DIR / 'reporters.json'
ISSUES_FILE = settings.BASE_DIR / 'issues.json'


def _load_data(file_path: Path):
    if not file_path.exists():
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _save_data(file_path: Path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


@csrf_exempt
def reporter_list_create(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)

        required_fields = ['id', 'name', 'email', 'team']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f"Missing required field: '{field}'"}, status=400)

        try:
            reporter = Reporter(
                id=int(data['id']),
                name=data['name'],
                email=data['email'],
                team=data['team']
            )
            reporter.validate()
        except ValueError as err:
            return JsonResponse({'error': str(err)}, status=400)
        except Exception as err:
            return JsonResponse({'error': f"Validation error: {str(err)}"}, status=400)

        reporters = _load_data(REPORTERS_FILE)
        reporter_dict = reporter.to_dict()

        # Update if existing id, else append
        existing_index = next((i for i, r in enumerate(reporters) if r.get('id') == reporter.id), None)
        if existing_index is not None:
            reporters[existing_index] = reporter_dict
        else:
            reporters.append(reporter_dict)

        _save_data(REPORTERS_FILE, reporters)
        return JsonResponse(reporter_dict, status=201)

    elif request.method == 'GET':
        reporters = _load_data(REPORTERS_FILE)
        id_param = request.GET.get('id')

        if id_param is not None:
            try:
                reporter_id = int(id_param)
            except ValueError:
                return JsonResponse({'error': 'Invalid id parameter'}, status=400)

            for reporter in reporters:
                if reporter.get('id') == reporter_id:
                    return JsonResponse(reporter, status=200)
            return JsonResponse({'error': 'Reporter not found'}, status=404)

        return JsonResponse(reporters, safe=False, status=200)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def issue_list_create(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)

        required_fields = ['id', 'title', 'description', 'status', 'priority', 'reporter_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f"{field.capitalize()} cannot be empty" if field == 'title' else f"Missing required field: '{field}'"}, status=400)

        priority = data.get('priority')
        try:
            if priority == 'critical':
                issue = CriticalIssue(
                    id=int(data['id']),
                    title=data['title'],
                    description=data['description'],
                    status=data['status'],
                    priority=data['priority'],
                    reporter_id=int(data['reporter_id']),
                    created_at=data.get('created_at')
                )
            elif priority == 'low':
                issue = LowPriorityIssue(
                    id=int(data['id']),
                    title=data['title'],
                    description=data['description'],
                    status=data['status'],
                    priority=data['priority'],
                    reporter_id=int(data['reporter_id']),
                    created_at=data.get('created_at')
                )
            else:
                issue = Issue(
                    id=int(data['id']),
                    title=data['title'],
                    description=data['description'],
                    status=data['status'],
                    priority=data['priority'],
                    reporter_id=int(data['reporter_id']),
                    created_at=data.get('created_at')
                )

            issue.validate()
        except ValueError as err:
            return JsonResponse({'error': str(err)}, status=400)
        except Exception as err:
            return JsonResponse({'error': f"Validation error: {str(err)}"}, status=400)

        response_data = issue.to_dict()
        response_data['message'] = issue.describe()

        issues = _load_data(ISSUES_FILE)
        existing_index = next((i for i, item in enumerate(issues) if item.get('id') == issue.id), None)
        if existing_index is not None:
            issues[existing_index] = response_data
        else:
            issues.append(response_data)

        _save_data(ISSUES_FILE, issues)
        return JsonResponse(response_data, status=201)

    elif request.method == 'GET':
        issues = _load_data(ISSUES_FILE)
        id_param = request.GET.get('id')
        status_param = request.GET.get('status')

        if id_param is not None:
            try:
                issue_id = int(id_param)
            except ValueError:
                return JsonResponse({'error': 'Invalid id parameter'}, status=400)

            for issue in issues:
                if issue.get('id') == issue_id:
                    return JsonResponse(issue, status=200)
            return JsonResponse({'error': 'Issue not found'}, status=404)

        if status_param is not None:
            filtered_issues = [issue for issue in issues if issue.get('status') == status_param]
            return JsonResponse(filtered_issues, safe=False, status=200)

        return JsonResponse(issues, safe=False, status=200)

    return JsonResponse({'error': 'Method not allowed'}, status=405)
