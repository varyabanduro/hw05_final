from django import forms
from .models import Comment, Group, Post


class PostForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea,
        label='Введите текст',
        help_text='Напишите пост тут'
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label='Выберите группу',
        help_text='Выберите группу, к которой относится пост'
    )

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Введите текст', 'group': 'Выберите группу'}
        help_texts = {
            'text': 'Напишите пост тут',
            'group': 'Выберите группу, к которой относится пост',
        }


class CommentForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea,
        label='Введите текст',
        help_text='Напишите комментарий тут'
    )

    class Meta:
        model = Comment
        fields = ('text',)
