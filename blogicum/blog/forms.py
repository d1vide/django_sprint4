from django import forms

from .models import Post, Comment


class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author', 'is_published')
        widgets = {
            'pub_date': forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={'type': 'datetime-local', 'class': 'form-control'},
            )
        }


class CommentCreateForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
