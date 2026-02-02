from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Exam, University


class CustomUserCreationForm(UserCreationForm):
    """
    カスタムユーザー登録フォーム
    """
    email = forms.EmailField(
        required=True,
        label='メールアドレス',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com'
        })
    )
    
    username = forms.CharField(
        label='ユーザー名',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ユーザー名を入力'
        })
    )
    
    password1 = forms.CharField(
        label='パスワード',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'パスワードを入力'
        })
    )
    
    password2 = forms.CharField(
        label='パスワード（確認）',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'もう一度パスワードを入力'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    カスタムログインフォーム
    """
    username = forms.CharField(
        label='ユーザー名',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ユーザー名',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label='パスワード',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'パスワード'
        })
    )

class ExamSearchForm(forms.Form):

    university = forms.ModelChoiceField(
        queryset=University.objects.all(),
        required=False,
        label='大学',
        empty_label='大学を選択または入力...',
        widget=forms.Select(attrs={
            'class': 'form-select select2-enable',  # JSでフックするためのクラスを追加
            'data-placeholder': '大学名を検索...'
        })
    )


class ExamCreateForm(forms.ModelForm):
    """
    過去問新規登録フォーム
    """
    class Meta:
        model = Exam
        fields = ['university', 'department', 'year', 'subject', 'exam_type', 'problem_url']
        widgets = {
            'university': forms.Select(attrs={
                'class': 'form-select',
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例: 工学部、法学部、理学部 数学科',
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '例: 2024',
                'min': 2000,
                'max': 2030,
            }),
            'subject': forms.Select(attrs={
                'class': 'form-select',
            }),
            'exam_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例: 一般入試、推薦入試、共通テスト',
            }),
            'problem_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...',
            }),
        }

    def clean(self):
        """
        フォーム全体のバリデーション
        同じ大学・年度・科目・試験種別の組み合わせが既に存在する場合はエラー
        """
        cleaned_data = super().clean()
        university = cleaned_data.get('university')
        year = cleaned_data.get('year')
        subject = cleaned_data.get('subject')
        exam_type = cleaned_data.get('exam_type')

        # 必須フィールドがすべて入力されている場合のみチェック
        if university and year and subject and exam_type:
            # 既存のレコードをチェック（編集時は自分自身を除外）
            existing = Exam.objects.filter(
                university=university,
                year=year,
                subject=subject,
                exam_type=exam_type
            )

            # 新規作成時（pk がない場合）のみチェック
            if self.instance.pk is None and existing.exists():
                raise forms.ValidationError(
                    f'この過去問は既に登録されています。（{university.name} {year}年度 {dict(Exam.SUBJECT_CHOICES).get(subject)} {exam_type}）'
                )

        return cleaned_data