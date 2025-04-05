from django.contrib.auth import get_user_model, authenticate, login, logout
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .serializers import UserRegistrationSerializer, UserLoginSerializer, StudentSerializer, ParentSerializer
from .models import Student, Parent

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Registration successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            
            if user:
                login(request, user)
                return Response({
                    'message': 'Login successful',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'user_type': user.user_type
                    }
                })
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({
            'message': 'Logged out successfully'
        })

class StudentProfileView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if Student.objects.filter(user=user).exists():
            return Response({
                'error': 'Student profile already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        student_data = {
            'user': user.id,
            'first_name': request.data.get('first_name'),
            'last_name': request.data.get('last_name'),
            'grade': request.data.get('grade'),
            'school_name': request.data.get('school_name'),
            'date_of_birth': request.data.get('date_of_birth'),
            'phone_number': request.data.get('phone_number'),
            'address': request.data.get('address'),
            'parent_name': request.data.get('parent_name'),
            'parent_email': request.data.get('parent_email'),
            'parent_phone': request.data.get('parent_phone')
        }
        
        serializer = StudentSerializer(data=student_data)
        if serializer.is_valid():
            student = serializer.save()
            user.user_type = 'student'
            user.save()
            
            return Response({
                'message': 'Student profile created successfully',
                'profile': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        user_id = request.query_params.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            student = Student.objects.get(user=user)
            serializer = StudentSerializer(student)
            return Response(serializer.data)
        except (User.DoesNotExist, Student.DoesNotExist):
            return Response({
                'error': 'Student profile not found'
            }, status=status.HTTP_404_NOT_FOUND)

class ParentProfileView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if Parent.objects.filter(user=user).exists():
            return Response({
                'error': 'Parent profile already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create parent_data dictionary with all fields
        parent_data = request.data.copy()
        parent_data['user'] = user.id  # Make sure user ID is included
        
        serializer = ParentSerializer(data=parent_data)
        if serializer.is_valid():
            parent = serializer.save()
            user.user_type = 'parent'
            user.save()
            
            return Response({
                'message': 'Parent profile created successfully',
                'profile': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        user_id = request.query_params.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            parent = Parent.objects.get(user=user)
            serializer = ParentSerializer(parent)
            return Response(serializer.data)
        except (User.DoesNotExist, Parent.DoesNotExist):
            return Response({
                'error': 'Parent profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
