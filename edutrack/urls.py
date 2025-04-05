from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('account.urls')),
    path('api/path/', include('path.urls')),
    path('api/tasks/', include('tasks.urls')),
]
