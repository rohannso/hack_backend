from rest_framework import serializers
from .models import LearningPath

class LearningPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningPath
        fields = ['student', 'path_data', 'created_at']
