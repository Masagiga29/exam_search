from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    # ホーム・検索画面
    path('', views.HomeView.as_view(), name='home'),
    
    # 検索結果一覧
    path('search/', views.ExamSearchView.as_view(), name='search'),
    
    # 過去問新規登録
    path('exam/create/', views.ExamCreateView.as_view(), name='exam_create'),

    # 過去問詳細・比較画面
    path('exam/<int:pk>/', views.ExamDetailView.as_view(), name='exam_detail'),
    
    # 大学詳細（その大学の過去問一覧）
    path('university/<int:pk>/', views.UniversityDetailView.as_view(), name='university_detail'),
    
    # マイページ
    path('mypage/', views.MyPageView.as_view(), name='mypage'),
    
    # お気に入り機能
    path('favorite/add/<int:exam_id>/', views.add_favorite, name='add_favorite'),
    path('favorite/remove/<int:exam_id>/', views.remove_favorite, name='remove_favorite'),
]
