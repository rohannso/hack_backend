from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Task(models.Model):
    title = models.CharField(max_length=200)
    task_type = models.CharField(max_length=20, choices=[
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('interactive', 'Interactive')
    ])
    learning_objective = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=20, choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ])
    content = models.JSONField()
    created_at = models.DateField(auto_now_add=True)  # Changed to DateField
    status = models.CharField(max_length=20, default='active')

class StudentTask(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    learning_path = models.ForeignKey('path.LearningPath', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='pending')
    score = models.IntegerField(null=True, blank=True)
    time_spent = models.DurationField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    started_at = models.DateField(null=True, blank=True)  # Changed to DateField
    completed_at = models.DateField(null=True, blank=True)  # Changed to DateField
    due_date = models.DateField()  # Changed to DateField

class Progress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    learning_path = models.ForeignKey('path.LearningPath', on_delete=models.CASCADE)
    total_tasks = models.IntegerField(default=0)
    completed_tasks = models.IntegerField(default=0)
    average_score = models.FloatField(default=0)
    total_time_spent = models.IntegerField(default=0)  # in minutes
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'learning_path']

class Badge(models.Model):
    BADGE_TYPES = (
        ('achievement', 'Achievement'),
        ('milestone', 'Milestone'),
        ('skill', 'Skill'),
    )

    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        null=True,  # Make the field nullable
        blank=True  # Allow blank in forms
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES, default='achievement')
    image_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    criteria = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.student:
            return f"{self.name} - {self.student.username}"
        return self.name

class StudentBadge(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'badge']

class StudentPoints(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student']
