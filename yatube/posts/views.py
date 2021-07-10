from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(20)
def index(request):
    post_list = Post.objects.select_related('author').all()
    paginator = Paginator(post_list, settings.PAGINATOR_YA)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html',
                  {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, settings.PAGINATOR_YA)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'group': group,
        'posts': posts,
        'page': page,
        'paginator': paginator
    }
    return render(request, 'group.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author)
    paginator = Paginator(post_list, settings.PAGINATOR_YA)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = request.user.is_authenticated and (
        Follow.objects.filter(user=request.user,
                              author=author).exists())
    context = {
        'author': author,
        'page': page,
        'post_count': post_list.count(),
        'paginator': paginator,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post.objects.select_related('author'),
                             id=post_id, author__username=username)
    post_count = Post.objects.filter(author=post.author).count()
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'author': post.author,
        'post': post,
        'post_count': post_count,
        'comments': comments,
        'form': form
    }
    return render(request, 'posts/post.html', context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        blank = form.save(commit=False)
        blank.author = request.user
        blank.save()
        return redirect('index')
    return render(request, 'posts/new_post.html',
                  {'form': form, 'rename': 'add'})


@login_required
def edit_post(request, username, post_id):
    post_object = get_object_or_404(Post,
                                    id=post_id,
                                    author__username=username)
    if request.user.username != username:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post_object)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'posts/new_post.html',
                  {'form': form,
                   'rename': 'edit',
                   'post_object': post_object})


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required()
def add_comment(request, username, post_id):
    post = get_object_or_404(Post,
                             id=post_id,
                             author__username=username)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('post', username, post_id)
    return render(request, 'includes/comments.html',
                  {'form': form, 'comments': comments, 'post': post})


@login_required
def follow_index(request):
    user = request.user
    post_list = Post.objects.filter(author__following__user=user)
    paginator = Paginator(post_list, settings.PAGINATOR_YA)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html',
                  {'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(author=author,
                                     user=user)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author).delete()
    return redirect('profile', username=username)
