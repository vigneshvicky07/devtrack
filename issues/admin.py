from django.contrib import admin
from issues.models import ReporterModel, IssueModel


@admin.register(ReporterModel)
class ReporterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'team')
    search_fields = ('name', 'email', 'team')


@admin.register(IssueModel)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'priority', 'reporter_id', 'created_at')
    list_filter = ('status', 'priority')
    search_fields = ('title', 'description')
