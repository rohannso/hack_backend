from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class LearningPath(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    path_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Learning Path for {self.student.username}"
