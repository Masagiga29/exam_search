from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm


class SignUpView(CreateView):
    
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('exams:home')

    def form_valid(self, form):
        
        user = form.save()
        
        login(self.request, user)
        return redirect(self.success_url)
