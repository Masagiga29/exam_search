from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class University(models.Model):
    """
    大学・高校情報を管理するモデル
    """
    name = models.CharField(
        max_length=200,
        verbose_name="学校名",
        help_text="大学名または高校名"
    )
    name_kana = models.CharField(
        max_length=200,
        verbose_name="学校名（かな）",
        blank=True,
        help_text="検索用のかな表記"
    )
    school_type = models.CharField(
        max_length=20,
        choices=[
            ('university', '大学'),
            ('high_school', '高校'),
        ],
        default='university',
        verbose_name="学校種別"
    )
    official_url = models.URLField(
        blank=True,
        verbose_name="公式サイトURL"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        verbose_name = "学校"
        verbose_name_plural = "学校一覧"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('exams:university_detail', kwargs={'pk': self.pk})


class Exam(models.Model):
    """
    過去問情報を管理するモデル
    年度、科目、問題PDFへのリンクなどを保持
    """
    SUBJECT_CHOICES = [
        ('japanese', '国語'),
        ('math', '数学'),
        ('english', '英語'),
        ('science', '理科'),
        ('social', '社会'),
        ('physics', '物理'),
        ('chemistry', '化学'),
        ('biology', '生物'),
        ('geography', '地理'),
        ('history', '歴史'),
        ('other', 'その他'),
    ]

    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='exams',
        verbose_name="学校"
    )
    year = models.IntegerField(
        verbose_name="年度",
        help_text="実施年度（例: 2024）"
    )
    subject = models.CharField(
        max_length=50,
        choices=SUBJECT_CHOICES,
        verbose_name="科目"
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="学部・学科",
        help_text="例: 工学部、法学部、理学部 数学科"
    )
    exam_type = models.CharField(
        max_length=50,
        verbose_name="試験種別",
        help_text="例: 一般入試、推薦入試、共通テスト",
        default="一般入試"
    )
    problem_url = models.URLField(
        verbose_name="問題PDF URL",
        help_text="大学公式または信頼できるソースの問題PDFリンク",
        blank=True
    )
    description = models.TextField(
        blank=True,
        verbose_name="説明",
        help_text="問題の概要や特記事項"
    )
    
    # メタデータ
    source_type = models.CharField(
        max_length=50,
        choices=[
            ('official', '大学公式'),
            ('yobi_school', '予備校'),
            ('archive', 'アーカイブサイト'),
            ('other', 'その他'),
        ],
        default='official',
        verbose_name="ソース種別"
    )
    scraped_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="取得日時",
        help_text="データを取得・確認した日時"
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name="検証済み",
        help_text="リンク切れチェック済み"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        verbose_name = "過去問"
        verbose_name_plural = "過去問一覧"
        ordering = ['-year', 'university__name', 'subject']
        unique_together = ['university', 'year', 'subject', 'exam_type']

    def __str__(self):
        return f"{self.university.name} {self.year}年度 {self.get_subject_display()}"

    def get_absolute_url(self):
        return reverse('exams:exam_detail', kwargs={'pk': self.pk})


class AnswerSource(models.Model):
    """
    予備校や教育機関が提供する解答・解説情報を管理するモデル
    同一の過去問に対して複数の解答ソースを紐付けることで横並び比較を実現
    """
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='answer_sources',
        verbose_name="過去問"
    )
    provider_name = models.CharField(
        max_length=100,
        verbose_name="提供元名",
        help_text="例: 河合塾、駿台予備校、東進ハイスクール"
    )
    answer_url = models.URLField(
        verbose_name="解答URL",
        help_text="解答・解説ページへのリンク"
    )
    has_detailed_explanation = models.BooleanField(
        default=False,
        verbose_name="詳細解説あり",
        help_text="詳しい解説が含まれているか"
    )
    has_video_explanation = models.BooleanField(
        default=False,
        verbose_name="動画解説あり"
    )
    reliability_score = models.IntegerField(
        default=5,
        verbose_name="信頼度スコア",
        help_text="1-10の範囲で評価（10が最高）"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="備考",
        help_text="解答の特徴や注意事項"
    )
    
    # メタデータ
    last_checked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="最終確認日時",
        help_text="リンクが有効であることを最後に確認した日時"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="有効",
        help_text="リンク切れの場合はFalseに設定"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        verbose_name = "解答ソース"
        verbose_name_plural = "解答ソース一覧"
        ordering = ['-reliability_score', 'provider_name']

    def __str__(self):
        return f"{self.provider_name} - {self.exam}"


class SearchHistory(models.Model):
    """
    ユーザーの検索履歴を記録するモデル（任意機能）
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='search_history',
        verbose_name="ユーザー"
    )
    query = models.CharField(
        max_length=200,
        verbose_name="検索クエリ"
    )
    filters = models.JSONField(
        default=dict,
        verbose_name="フィルター条件",
        help_text="年度、科目などの絞り込み条件をJSON形式で保存"
    )
    searched_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="検索日時"
    )

    class Meta:
        verbose_name = "検索履歴"
        verbose_name_plural = "検索履歴一覧"
        ordering = ['-searched_at']

    def __str__(self):
        return f"{self.user.username} - {self.query} ({self.searched_at})"


class Favorite(models.Model):
    """
    ユーザーのお気に入り過去問を管理するモデル（任意機能）
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name="ユーザー"
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name="過去問"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="お気に入り登録日時"
    )
    note = models.TextField(
        blank=True,
        verbose_name="メモ",
        help_text="個人的なメモ"
    )

    class Meta:
        verbose_name = "お気に入り"
        verbose_name_plural = "お気に入り一覧"
        unique_together = ['user', 'exam']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.exam}"
