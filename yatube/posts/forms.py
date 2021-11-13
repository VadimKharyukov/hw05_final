from django import forms
from django.forms import ModelForm

from .models import Comment, Post, Group


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {'text': 'Введите текст записи',
                      'group': 'Выберите группу',
                      'image': 'Загрузите изображение'}
        labels = {'text': 'Введите текст',
                  'group': 'Выберите группу',
                  'image': 'Загрузите картинку'}
        widgets = {'text': forms.Textarea()}


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ('title', 'slug', 'description')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        comment = forms.CharField(widget=forms.Textarea)
