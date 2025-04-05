from django.db import models
from django.conf import settings

# Create your models here.
class LearningPath(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # User model (or Student model if separate)
    path_data = models.JSONField()  # Save the learning path as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Learning Path for {self.student.username} at {self.created_at}"
