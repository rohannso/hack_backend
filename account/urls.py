from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/student/', views.StudentProfileView.as_view(), name='student-profile'),
    path('profile/parent/', views.ParentProfileView.as_view(), name='parent-profile'),
]



