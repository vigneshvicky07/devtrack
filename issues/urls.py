from django.urls import path
from issues import views

urlpatterns = [
    path('reporters/', views.reporter_list_create, name='reporter_list_create'),
    path('issues/', views.issue_list_create, name='issue_list_create'),
]
