from django.contrib import admin
from .models import University, Exam, AnswerSource, SearchHistory, Favorite


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    """
    大学管理画面
    """
    list_display = ('name', 'name_kana', 'school_type', 'exam_count', 'created_at')
    list_filter = ('school_type', 'created_at')
    search_fields = ('name', 'name_kana')
    ordering = ('name',)
    
    def exam_count(self, obj):
        return obj.exams.count()
    exam_count.short_description = '過去問数'


class AnswerSourceInline(admin.TabularInline):
    """
    Examの詳細画面でAnswerSourceを編集できるようにするインライン
    """
    model = AnswerSource
    extra = 1
    fields = ('provider_name', 'answer_url', 'has_detailed_explanation', 
              'has_video_explanation', 'reliability_score', 'is_active')


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    """
    過去問管理画面
    """
    list_display = ('university', 'year', 'subject', 'exam_type', 
                    'source_type', 'is_verified', 'answer_sources_count', 'created_at')
    list_filter = ('year', 'subject', 'exam_type', 'source_type', 'is_verified')
    search_fields = ('university__name', 'description')
    ordering = ('-year', 'university__name')
    date_hierarchy = 'created_at'
    
    inlines = [AnswerSourceInline]
    
    fieldsets = (
        ('基本情報', {
            'fields': ('university', 'year', 'subject', 'exam_type')
        }),
        ('詳細情報', {
            'fields': ('description', 'problem_url')
        }),
        ('メタデータ', {
            'fields': ('source_type', 'scraped_at', 'is_verified'),
            'classes': ('collapse',)
        }),
    )
    
    def answer_sources_count(self, obj):
        return obj.answer_sources.filter(is_active=True).count()
    answer_sources_count.short_description = '解答ソース数'


@admin.register(AnswerSource)
class AnswerSourceAdmin(admin.ModelAdmin):
    """
    解答ソース管理画面
    """
    list_display = ('provider_name', 'exam', 'has_detailed_explanation', 
                    'has_video_explanation', 'reliability_score', 'is_active', 'last_checked_at')
    list_filter = ('provider_name', 'has_detailed_explanation', 
                   'has_video_explanation', 'is_active')
    search_fields = ('provider_name', 'exam__university__name', 'notes')
    ordering = ('-reliability_score', 'provider_name')
    
    fieldsets = (
        ('基本情報', {
            'fields': ('exam', 'provider_name', 'answer_url')
        }),
        ('解答の特徴', {
            'fields': ('has_detailed_explanation', 'has_video_explanation', 
                      'reliability_score', 'notes')
        }),
        ('ステータス', {
            'fields': ('is_active', 'last_checked_at')
        }),
    )


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    """
    検索履歴管理画面
    """
    list_display = ('user', 'query', 'searched_at')
    list_filter = ('searched_at',)
    search_fields = ('user__username', 'query')
    ordering = ('-searched_at',)
    date_hierarchy = 'searched_at'
    
    readonly_fields = ('user', 'query', 'filters', 'searched_at')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    お気に入り管理画面
    """
    list_display = ('user', 'exam', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'exam__university__name')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    readonly_fields = ('created_at',)
