from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tasks', views.TaskViewSet)
router.register(r'student-tasks', views.StudentTaskViewSet, basename='student-task')
router.register(r'progress', views.ProgressViewSet, basename='progress')
router.register(r'badges', views.BadgeViewSet, basename='badge')
router.register(r'student-badges', views.StudentBadgeViewSet, basename='student-badge')
router.register(r'student-points', views.StudentPointsViewSet, basename='student-points')

urlpatterns = [
    path('', include(router.urls)),
    path('create-tasks/', views.create_tasks_for_learning_path, name='create-tasks'),
    path('weekly-report/', views.get_student_weekly_report, name='weekly-report'),
    path('monthly-report/', views.get_student_monthly_report, name='monthly-report'),
]
