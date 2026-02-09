
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts.views import SignUpView
from exams.forms import CustomAuthenticationForm

urlpatterns = [
   
    path('admin/', admin.site.urls),
    
    
    path('accounts/login/', 
         auth_views.LoginView.as_view(authentication_form=CustomAuthenticationForm), 
         name='login'),
    path('accounts/logout/', 
         auth_views.LogoutView.as_view(next_page='exams:home'), 
         name='logout'),
    path('accounts/signup/', SignUpView.as_view(), name='signup'),
    
    
    path('', include('exams.urls')),
]
