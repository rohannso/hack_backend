from rest_framework import serializers
from .models import Task, StudentTask, Progress, Badge, StudentBadge, StudentPoints

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'task_type', 'learning_objective', 'difficulty', 'content']

    def validate(self, data):
        """
        Validate the task data.
        """
        # Validate task_type
        valid_task_types = ['quiz', 'assignment', 'interactive']
        if data.get('task_type') not in valid_task_types:
            raise serializers.ValidationError({
                'task_type': f'Task type must be one of {valid_task_types}'
            })

        # Validate difficulty
        valid_difficulties = ['easy', 'medium', 'hard']
        if data.get('difficulty') not in valid_difficulties:
            raise serializers.ValidationError({
                'difficulty': f'Difficulty must be one of {valid_difficulties}'
            })

        # Validate content structure based on task type
        content = data.get('content', {})
        if not isinstance(content, dict):
            raise serializers.ValidationError({
                'content': 'Content must be a JSON object'
            })

        if data['task_type'] == 'quiz':
            if 'questions' not in content:
                raise serializers.ValidationError({
                    'content': 'Quiz content must include questions'
                })

        elif data['task_type'] == 'assignment':
            if 'instructions' not in content:
                raise serializers.ValidationError({
                    'content': 'Assignment content must include instructions'
                })

        elif data['task_type'] == 'interactive':
            if 'activity_type' not in content:
                raise serializers.ValidationError({
                    'content': 'Interactive content must include activity_type'
                })

        return data

class StudentTaskSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    
    class Meta:
        model = StudentTask
        fields = ['id', 'task', 'status', 'score', 'time_spent', 'feedback', 
                 'started_at', 'completed_at', 'due_date']

class ProgressSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Progress
        fields = ['id', 'student', 'learning_path', 'total_tasks', 'completed_tasks',
                 'average_score', 'total_time_spent', 'last_updated', 'progress_percentage']
    
    def get_progress_percentage(self, obj):
        return obj.calculate_progress_percentage()

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['id', 'name', 'description', 'badge_type', 'image_url', 
                 'created_at', 'criteria']
        read_only_fields = ['created_at']

class StudentBadgeSerializer(serializers.ModelSerializer):
    badge_name = serializers.ReadOnlyField(source='badge.name')
    badge_description = serializers.ReadOnlyField(source='badge.description')
    badge_icon = serializers.ReadOnlyField(source='badge.icon')
    
    class Meta:
        model = StudentBadge
        fields = ['id', 'student', 'badge', 'badge_name', 'badge_description', 
                 'badge_icon', 'earned_at']

class StudentPointsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentPoints
        fields = '__all__'
