import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from issues.models import (
    Reporter,
    Issue,
    CriticalIssue,
    LowPriorityIssue,
    ReporterModel,
    IssueModel,
)


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

        record, _ = ReporterModel.objects.update_or_create(
            id=reporter.id,
            defaults={
                'name': reporter.name,
                'email': reporter.email,
                'team': reporter.team,
            }
        )
        return JsonResponse(record.to_dict(), status=201)

    elif request.method == 'GET':
        id_param = request.GET.get('id')

        if id_param is not None:
            try:
                reporter_id = int(id_param)
            except ValueError:
                return JsonResponse({'error': 'Invalid id parameter'}, status=400)

            record = ReporterModel.objects.filter(id=reporter_id).first()
            if record:
                return JsonResponse(record.to_dict(), status=200)
            return JsonResponse({'error': 'Reporter not found'}, status=404)

        reporters = [r.to_dict() for r in ReporterModel.objects.all()]
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

        record, _ = IssueModel.objects.update_or_create(
            id=issue.id,
            defaults={
                'title': issue.title,
                'description': issue.description,
                'status': issue.status,
                'priority': issue.priority,
                'reporter_id': issue.reporter_id,
                'created_at': str(issue.created_at),
                'message': issue.describe(),
            }
        )
        return JsonResponse(record.to_dict(), status=201)

    elif request.method == 'GET':
        id_param = request.GET.get('id')
        status_param = request.GET.get('status')

        if id_param is not None:
            try:
                issue_id = int(id_param)
            except ValueError:
                return JsonResponse({'error': 'Invalid id parameter'}, status=400)

            record = IssueModel.objects.filter(id=issue_id).first()
            if record:
                return JsonResponse(record.to_dict(), status=200)
            return JsonResponse({'error': 'Issue not found'}, status=404)

        records = IssueModel.objects.all()
        if status_param is not None:
            records = records.filter(status=status_param)

        return JsonResponse([r.to_dict() for r in records], safe=False, status=200)

    return JsonResponse({'error': 'Method not allowed'}, status=405)
