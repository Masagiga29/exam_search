from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView, CreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse

from .models import Exam, University, AnswerSource, SearchHistory, Favorite
from .forms import ExamSearchForm, ExamCreateForm


class HomeView(TemplateView):
    """
    ホーム画面 - 検索バーと人気の大学・最新の過去問を表示
    """
    template_name = 'exams/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ExamSearchForm()
        context['popular_universities'] = University.objects.annotate(
            exam_count=Count('exams')
        ).order_by('-exam_count')[:6]
        context['recent_exams'] = Exam.objects.select_related(
            'university'
        ).order_by('-created_at')[:8]
        return context


class ExamSearchView(ListView):
    """
    検索結果一覧画面 - 絞り込み検索機能付き
    """
    model = Exam
    template_name = 'exams/search_results.html'
    context_object_name = 'exams'
    paginate_by = 12

    def get_queryset(self):
        queryset = Exam.objects.select_related('university').prefetch_related('answer_sources')
        
        # 検索クエリパラメータの取得
        query = self.request.GET.get('q', '')
        university_id = self.request.GET.get('university', '')
        year = self.request.GET.get('year', '')
        subject = self.request.GET.get('subject', '')
        
        # キーワード検索（大学名、説明文）
        if query:
            queryset = queryset.filter(
                Q(university__name__icontains=query) |
                Q(university__name_kana__icontains=query) |
                Q(description__icontains=query)
            )
        
        # 大学による絞り込み
        if university_id:
            queryset = queryset.filter(university_id=university_id)
        
        # 年度による絞り込み
        if year:
            queryset = queryset.filter(year=year)
        
        # 科目による絞り込み
        if subject:
            queryset = queryset.filter(subject=subject)
        
        # 検索履歴の保存（ログインユーザーのみ）
        if self.request.user.is_authenticated and query:
            SearchHistory.objects.create(
                user=self.request.user,
                query=query,
                filters={
                    'university_id': university_id,
                    'year': year,
                    'subject': subject,
                }
            )
        
        return queryset.order_by('-year', 'university__name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ExamSearchForm(self.request.GET)
        context['query'] = self.request.GET.get('q', '')
        context['total_results'] = self.get_queryset().count()
        
        # 絞り込み用の選択肢
        context['universities'] = University.objects.all()
        context['years'] = Exam.objects.values_list('year', flat=True).distinct().order_by('-year')
        context['subjects'] = Exam.SUBJECT_CHOICES
        
        return context


class ExamDetailView(DetailView):
    """
    過去問詳細画面 - 問題PDFプレビューと予備校別解答の比較テーブル
    """
    model = Exam
    template_name = 'exams/exam_detail.html'
    context_object_name = 'exam'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 予備校別解答ソースを取得（信頼度順）
        context['answer_sources'] = self.object.answer_sources.filter(
            is_active=True
        ).order_by('-reliability_score', 'provider_name')
        
        # 同じ大学・年度の他の科目を取得
        context['related_exams'] = Exam.objects.filter(
            university=self.object.university,
            year=self.object.year
        ).exclude(pk=self.object.pk).select_related('university')
        
        # お気に入り状態の確認（ログインユーザーのみ）
        if self.request.user.is_authenticated:
            context['is_favorited'] = Favorite.objects.filter(
                user=self.request.user,
                exam=self.object
            ).exists()
        else:
            context['is_favorited'] = False
        
        return context


class UniversityDetailView(DetailView):
    """
    大学詳細画面 - その大学の過去問一覧
    """
    model = University
    template_name = 'exams/university_detail.html'
    context_object_name = 'university'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 年度別・科目別の過去問を取得
        context['exams_by_year'] = {}
        exams = self.object.exams.select_related('university').order_by('-year', 'subject')
        
        for exam in exams:
            if exam.year not in context['exams_by_year']:
                context['exams_by_year'][exam.year] = []
            context['exams_by_year'][exam.year].append(exam)
        
        return context


class ExamCreateView(LoginRequiredMixin, CreateView):
    """
    過去問新規登録画面 - ログインユーザーのみ利用可能
    """
    model = Exam
    form_class = ExamCreateForm
    template_name = 'exams/exam_form.html'
    login_url = '/accounts/login/'

    def form_valid(self, form):
        messages.success(self.request, '過去問を登録しました。')
        return super().form_valid(form)


class MyPageView(LoginRequiredMixin, TemplateView):
    """
    マイページ - 検索履歴とお気に入り一覧
    """
    template_name = 'exams/mypage.html'
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 最近の検索履歴（10件）
        context['search_history'] = SearchHistory.objects.filter(
            user=self.request.user
        ).order_by('-searched_at')[:10]
        
        # お気に入り一覧
        context['favorites'] = Favorite.objects.filter(
            user=self.request.user
        ).select_related('exam__university').order_by('-created_at')
        
        return context


@login_required
def add_favorite(request, exam_id):
    """
    お気に入りに追加
    """
    exam = get_object_or_404(Exam, pk=exam_id)
    
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        exam=exam
    )
    
    if created:
        messages.success(request, f'「{exam}」をお気に入りに追加しました。')
    else:
        messages.info(request, 'すでにお気に入りに登録されています。')
    
    return redirect('exams:exam_detail', pk=exam_id)


@login_required
def remove_favorite(request, exam_id):
    """
    お気に入りから削除
    """
    exam = get_object_or_404(Exam, pk=exam_id)
    
    deleted_count, _ = Favorite.objects.filter(
        user=request.user,
        exam=exam
    ).delete()
    
    if deleted_count > 0:
        messages.success(request, f'「{exam}」をお気に入りから削除しました。')
    else:
        messages.warning(request, 'お気に入りに登録されていません。')
    
    return redirect('exams:exam_detail', pk=exam_id)
