"""
exam_search プロジェクトのURLルーティング設定
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts.views import SignUpView
from exams.forms import CustomAuthenticationForm

urlpatterns = [
    # 管理画面
    path('admin/', admin.site.urls),
    
    # 認証関連
    path('accounts/login/', 
         auth_views.LoginView.as_view(authentication_form=CustomAuthenticationForm), 
         name='login'),
    path('accounts/logout/', 
         auth_views.LogoutView.as_view(next_page='exams:home'), 
         name='logout'),
    path('accounts/signup/', SignUpView.as_view(), name='signup'),
    
    # 過去問検索アプリ
    path('', include('exams.urls')),
]
