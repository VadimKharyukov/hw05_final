from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm, GroupForm
from .models import Follow, Group, Post, User, Ip, Comment


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@cache_page(20)
def index(request):
    post_list = Post.objects.select_related('group').all()
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


def group_list(request):
    group_lists = Group.objects.all()
    paginator = Paginator(group_lists, settings.PAGINATOR_YA)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/group_list.html', {
        'group_list': group_lists, 'page': page, 'paginator': paginator})


@login_required
def group_create(request):
    form = GroupForm(request.POST or None)
    if request.method == 'GET' or not form.is_valid():
        return render(request, 'posts/new_group.html',
                      {'form': form})
    group = form.save(commit=False)
    group.save()
    return redirect('group_list')


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
    ip = get_client_ip(request)
    if Ip.objects.filter(ip=ip).exists():
        post.views.add(Ip.objects.get(ip=ip))
    else:
        Ip.objects.create(ip=ip)
        post.views.add(Ip.objects.get(ip=ip))
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


@login_required
def comment_delete(request, id):
    comment = get_object_or_404(Comment, id=id)
    if request.user == comment.author or request.user == comment.post.author:
        comment.delete()
    return redirect('post', username=comment.post.author,
                    post_id=comment.post.id)


@login_required
def post_delete(request, id):
    post = get_object_or_404(Post, id=id)
    if request.user == post.author:
        post.delete()
        return redirect('profile', username=request.user)
