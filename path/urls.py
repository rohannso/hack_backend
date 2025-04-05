from django.urls import path
from .views import LearningPathView

urlpatterns = [
    path('generate_learning_path/', LearningPathView.as_view(), name='generate_learning_path'),
]
