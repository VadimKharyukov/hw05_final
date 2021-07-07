from django import forms
from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Введите текст',
                  'group': 'Выберите группу',
                  'image': 'Загрузите картинку'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        comment = forms.CharField(widget=forms.Textarea)
