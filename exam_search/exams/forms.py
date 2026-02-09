from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Exam, University


class CustomUserCreationForm(UserCreationForm):
    
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
        queryset=University.objects.order_by('name_kana', 'name'),
        required=False,
        label='大学',
        empty_label='大学を選択または入力...',
        widget=forms.Select(attrs={
            'class': 'form-select select2-enable',  
            'data-placeholder': '大学名を検索...'
        })
    )


class ExamCreateForm(forms.ModelForm):

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
       
        cleaned_data = super().clean()
        
        return cleaned_data