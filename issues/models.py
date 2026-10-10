from abc import ABC, abstractmethod
from datetime import datetime
from django.db import models


# ==============================================================================
# Domain Entities (OOP Models with Polymorphism & Business Logic)
# ==============================================================================

class BaseEntity(ABC):
    @abstractmethod
    def validate(self):
        pass

    def to_dict(self):
        return {
            key: value
            for key, value in self.__dict__.items()
        }


class Reporter(BaseEntity):
    def __init__(self, id, name, email, team):
        self.id = id
        self.name = name
        self.email = email
        self.team = team

    def validate(self):
        if not self.name:
            raise ValueError('Name cannot be empty')
        if not self.email or '@' not in str(self.email):
            raise ValueError('Invalid email')


class Issue(BaseEntity):
    ALLOWED_STATUSES = ['open', 'in_progress', 'resolved', 'closed']
    ALLOWED_PRIORITIES = ['low', 'medium', 'high', 'critical']

    def __init__(self, id, title, description, status, priority, reporter_id, created_at=None):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.reporter_id = reporter_id
        if created_at is None:
            self.created_at = str(datetime.now())
        else:
            self.created_at = created_at

    def validate(self):
        if not self.title:
            raise ValueError('Title cannot be empty')
        if self.status not in self.ALLOWED_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.ALLOWED_STATUSES)}")
        if self.priority not in self.ALLOWED_PRIORITIES:
            raise ValueError(f"Invalid priority. Must be one of: {', '.join(self.ALLOWED_PRIORITIES)}")

    def describe(self):
        return f"{self.title} [{self.priority}]"


class CriticalIssue(Issue):
    def describe(self):
        return f"[URGENT] {self.title} — needs immediate attention"


class LowPriorityIssue(Issue):
    def describe(self):
        return f"{self.title} — low priority, handle when free"


# ==============================================================================
# Django Database ORM Models (PostgreSQL Persistence)
# ==============================================================================

class ReporterModel(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    team = models.CharField(max_length=100)

    class Meta:
        db_table = 'reporters'
        verbose_name = 'Reporter'
        verbose_name_plural = 'Reporters'
        ordering = ['id']

    def __str__(self):
        return f"{self.name} ({self.team})"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'team': self.team,
        }


class IssueModel(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=50)
    priority = models.CharField(max_length=50)
    reporter_id = models.IntegerField()
    created_at = models.CharField(max_length=100)
    message = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'issues'
        verbose_name = 'Issue'
        verbose_name_plural = 'Issues'
        ordering = ['id']

    def __str__(self):
        return f"{self.title} [{self.priority}]"

    def to_dict(self):
        res = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'reporter_id': self.reporter_id,
            'created_at': self.created_at,
        }
        if self.message:
            res['message'] = self.message
        return res
