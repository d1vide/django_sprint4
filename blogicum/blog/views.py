from datetime import datetime

from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from .models import Category, Post, User, Comment
from .forms import CommentCreateForm, PostCreateForm

POSTS_ON_PAGE_COUNT = 10


def get_post_filter():
    return Post.objects.all().filter(is_published=True,
                                     category__is_published=True,
                                     pub_date__lte=datetime.now())


class PostPaginateMixin:
    model = Post
    paginate_by = POSTS_ON_PAGE_COUNT


class ProfileListView(PostPaginateMixin, ListView):
    template_name = 'blog/profile.html'

    def get_queryset(self):
        if str(self.request.user) == self.kwargs.get('username'):
            return Post.objects.filter(author__username=self.kwargs.get(
                'username')).annotate(comment_count=Count('comments')
                                      ).order_by('-pub_date')
        else:
            return get_post_filter().filter(
                author__username=self.kwargs.get(
                    'username')).annotate(comment_count=Count('comments')
                                          ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(User.objects.filter(
            username=self.kwargs.get('username')))
        context['comment_count'] = Comment.objects.annotate(
            comment_count=Count('post_id'))
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'blog/user.html'
    fields = ('first_name', 'last_name', 'username', 'email')
    success_url = reverse_lazy('blog:index')

    def get_object(self, queryset=None):
        return self.request.user


class PostActionMixin:
    model = Post
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user})


class PostCreateView(PostActionMixin, LoginRequiredMixin, CreateView):
    form_class = PostCreateForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(PostActionMixin, LoginRequiredMixin, UpdateView):
    fields = ('title', 'text', 'location', 'category', 'image')

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if (not request.user.is_authenticated
                or instance.author != self.request.user):
            return redirect('blog:post_detail', kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        posts = get_object_or_404(Post, pk=self.kwargs.get('pk'))
        return posts

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'pk': self.kwargs.get('pk')})


class PostDeleteView(PostActionMixin, LoginRequiredMixin, DeleteView):
    fields = ('title', 'text', 'location', 'category', )

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if instance.author != self.request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostCreateForm(self.request.POST or None,
                                         instance=self.object)
        return context


class PostListView(PostPaginateMixin, ListView):
    template_name = 'blog/index.html'

    def get_queryset(self):
        posts = get_post_filter().annotate(comment_count=Count('comments')
                                           ).order_by('-pub_date')
        return posts


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if instance.author == request.user:
            return super().dispatch(request, *args, **kwargs)
        else:
            instance = get_post_filter().filter(pk=kwargs['pk'])
            if not instance:
                raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentCreateForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class CategoryListView(PostPaginateMixin, ListView):
    template_name = 'blog/category.html'

    def get_queryset(self):
        page_obj = get_post_filter().filter(category__slug=self.kwargs.get(
            'slug')).annotate(comment_count=Count('comments')).order_by(
                '-pub_date')
        return page_obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(Category,
                                                slug=self.kwargs.get('slug'),
                                                is_published=True)
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentCreateForm

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'pk': self.kwargs.get('pk')})

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs.get('pk'))
        return super().form_valid(form)


class CommentUpdateDeleteMixin(LoginRequiredMixin):
    model = Comment
    fields = ('text', )
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        comment = get_object_or_404(Comment,
                                    id=self.kwargs.get('comment_pk'),
                                    author=self.request.user)
        return comment

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'pk': self.kwargs.get('pk')})


class CommentUpdateView(CommentUpdateDeleteMixin, UpdateView):
    pass


class CommentDeleteView(CommentUpdateDeleteMixin, DeleteView):
    pass
