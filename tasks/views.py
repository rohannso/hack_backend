import json
import logging
from django.db.models import Avg, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from .services import TaskGenerator, LLMTaskGenerator
from .serializers import TaskSerializer, StudentTaskSerializer, ProgressSerializer, BadgeSerializer, StudentBadgeSerializer, StudentPointsSerializer
from .models import Task, StudentTask, Progress, Badge, StudentBadge, StudentPoints
from path.models import LearningPath
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()
logger = logging.getLogger(__name__)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

class StudentTaskViewSet(viewsets.ModelViewSet):
    serializer_class = StudentTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all student tasks
        for the currently authenticated user.
        """
        user = self.request.user
        return StudentTask.objects.filter(student=user)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

class ProgressViewSet(viewsets.ModelViewSet):
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter progress records for the currently authenticated user
        """
        user = self.request.user
        return Progress.objects.filter(student=user)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

class StudentBadgeViewSet(viewsets.ModelViewSet):
    serializer_class = StudentBadgeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter student badges for the currently authenticated user
        """
        user = self.request.user
        return StudentBadge.objects.filter(student=user)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

class BadgeViewSet(viewsets.ModelViewSet):
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all badges
        that are available to the currently authenticated user.
        """
        return Badge.objects.all()

    def perform_create(self, serializer):
        serializer.save()

class StudentPointsViewSet(viewsets.ModelViewSet):
    serializer_class = StudentPointsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter points records for the currently authenticated user
        """
        user = self.request.user
        return StudentPoints.objects.filter(student=user)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

@api_view(['POST'])
def create_tasks_for_learning_path(request):
    """Create AI-generated tasks based on a learning path"""
    learning_path_id = request.data.get('learning_path_id')
    student_id = request.data.get('student_id')
    
    if not learning_path_id or not student_id:
        return Response(
            {'error': 'Both learning_path_id and student_id are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get the learning path and student
        learning_path = get_object_or_404(LearningPath, id=learning_path_id)
        student = get_object_or_404(User, id=student_id)
        
        logger.info(f"Generating tasks for learning path {learning_path_id} and student {student_id}")
        
        task_generator = TaskGenerator()
        all_tasks = []
        validation_errors = []
        
        # Get topics from learning path
        topics = learning_path.path_data.get('topics', [])
        if not topics:
            logger.warning("No topics found in learning path, generating generic tasks")
            topics = [{'title': 'General Learning', 'difficulty': 'medium'}]
        
        for topic in topics:
            topic_title = topic.get('title', 'General Learning')
            topic_difficulty = topic.get('difficulty', 'medium')
            student_grade = learning_path.path_data.get('student_grade', 'intermediate')
            
            logger.info(f"Processing topic: {topic_title} with difficulty: {topic_difficulty}")
            
            topic_tasks = task_generator.generate_tasks(
                learning_objective=topic_title,
                difficulty=topic_difficulty,
                student_grade=student_grade
            )
            all_tasks.extend(topic_tasks)
        
        if not all_tasks:
            logger.error("No tasks were generated")
            return Response({
                'error': 'Failed to generate tasks',
                'details': 'No tasks could be generated from the learning path'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create tasks in database
        created_tasks = []
        for task_data in all_tasks:
            try:
                # Calculate due date as a date object
                due_days = settings.TASK_GENERATION.get('DEFAULT_DUE_DAYS', 7)
                due_date = (timezone.now() + timezone.timedelta(days=due_days)).date()
                
                # Add necessary fields
                task_data.update({
                    'learning_path': learning_path.id,
                    'created_at': timezone.now().date(),  # Convert to date
                    'status': 'active'
                })
                
                logger.info(f"Creating task: {task_data['title']}")
                task_serializer = TaskSerializer(data=task_data)
                
                if task_serializer.is_valid():
                    task = task_serializer.save()
                    student_task = StudentTask.objects.create(
                        student=student,
                        task=task,
                        learning_path=learning_path,
                        due_date=due_date  # Use the calculated date object
                    )
                    created_tasks.append(StudentTaskSerializer(student_task).data)
                    logger.info(f"Successfully created task: {task.title}")
                else:
                    error_msg = f"Validation failed for task '{task_data.get('title')}': {task_serializer.errors}"
                    logger.error(error_msg)
                    validation_errors.append(error_msg)
            except Exception as e:
                error_msg = f"Error creating task '{task_data.get('title')}': {str(e)}"
                logger.error(error_msg)
                validation_errors.append(error_msg)
        
        if not created_tasks:
            return Response({
                'error': 'Failed to create tasks',
                'details': 'No valid tasks could be created',
                'validation_errors': validation_errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': f'Successfully created {len(created_tasks)} tasks',
            'tasks': created_tasks,
            'validation_errors': validation_errors if validation_errors else None
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error in create_tasks_for_learning_path: {str(e)}")
        return Response({
            'error': 'Failed to process request',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_student_weekly_report(request):
    """Generate a weekly report for the student"""
    student = request.user
    end_date = timezone.now().date()
    start_date = end_date - timezone.timedelta(days=7)
    
    # Get tasks completed in the last week
    completed_tasks = StudentTask.objects.filter(
        student=student,
        status='completed',
        completed_at__date__gte=start_date,
        completed_at__date__lte=end_date
    )
    
    # Generate report data
    report = {
        'period': f"{start_date} to {end_date}",
        'total_tasks_completed': completed_tasks.count(),
        'average_score': completed_tasks.aggregate(Avg('score'))['score__avg'] or 0,
        'total_time_spent': completed_tasks.aggregate(total=Sum('time_spent'))['total'] or 0,
        'tasks_by_subject': {},
        'tasks_details': StudentTaskSerializer(completed_tasks, many=True).data
    }
    
    # Group tasks by learning objective
    for task in completed_tasks:
        objective = task.task.learning_objective
        if objective not in report['tasks_by_subject']:
            report['tasks_by_subject'][objective] = {
                'count': 0,
                'avg_score': 0,
                'total_time': 0
            }
        
        report['tasks_by_subject'][objective]['count'] += 1
        report['tasks_by_subject'][objective]['avg_score'] += task.score
        report['tasks_by_subject'][objective]['total_time'] += task.time_spent
    
    # Calculate averages for each subject
    for subject in report['tasks_by_subject']:
        count = report['tasks_by_subject'][subject]['count']
        if count > 0:
            report['tasks_by_subject'][subject]['avg_score'] /= count
    
    return Response(report)

@api_view(['GET'])
def get_student_monthly_report(request):
    """Generate a monthly report for the student"""
    student = request.user
    end_date = timezone.now().date()
    start_date = end_date - timezone.timedelta(days=30)
    
    # Get tasks completed in the last month
    completed_tasks = StudentTask.objects.filter(
        student=student,
        status='completed',
        completed_at__date__gte=start_date,
        completed_at__date__lte=end_date
    )
    
    # Generate report data (similar to weekly report but with more trend analysis)
    report = {
        'period': f"{start_date} to {end_date}",
        'total_tasks_completed': completed_tasks.count(),
        'average_score': completed_tasks.aggregate(Avg('score'))['score__avg'] or 0,
        'total_time_spent': completed_tasks.aggregate(total=Sum('time_spent'))['total'] or 0,
        'weekly_breakdown': {},
        'subject_performance': {},
        'badges_earned': StudentBadgeSerializer(
            StudentBadge.objects.filter(
                student=student,
                earned_at__date__gte=start_date
            ), 
            many=True
        ).data
    }
    
    # Group by week
    for i in range(4):
        week_start = start_date + timezone.timedelta(days=i*7)
        week_end = week_start + timezone.timedelta(days=6)
        
        week_tasks = completed_tasks.filter(
            completed_at__date__gte=week_start,
            completed_at__date__lte=week_end
        )
        
        report['weekly_breakdown'][f"Week {i+1}"] = {
            'count': week_tasks.count(),
            'avg_score': week_tasks.aggregate(Avg('score'))['score__avg'] or 0
        }
    
    # Group by learning objective/subject
    for task in completed_tasks:
        objective = task.task.learning_objective
        if objective not in report['subject_performance']:
            report['subject_performance'][objective] = {
                'count': 0,
                'scores': [],
                'total_time': 0
            }
        
        report['subject_performance'][objective]['count'] += 1
        report['subject_performance'][objective]['scores'].append(task.score)
        report['subject_performance'][objective]['total_time'] += task.time_spent
    
    # Calculate statistics for each subject
    for subject in report['subject_performance']:
        scores = report['subject_performance'][subject]['scores']
        if scores:
            report['subject_performance'][subject]['avg_score'] = sum(scores) / len(scores)
            report['subject_performance'][subject]['min_score'] = min(scores)
            report['subject_performance'][subject]['max_score'] = max(scores)
            report['subject_performance'][subject].pop('scores')  # Remove raw scores
    
    return Response(report)
