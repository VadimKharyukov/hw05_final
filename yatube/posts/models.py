from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, F

User = get_user_model()


class Ip(models.Model):
    ip = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'Айпишки'
        verbose_name = 'Афпишка'

    def __str__(self):
        return self.ip


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, default='')
    description = models.TextField()

    class Meta:
        verbose_name_plural = 'Сообщества'
        verbose_name = 'Сообщество'
        ordering = ['title']

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True,
                              null=True, related_name='posts')
    text = models.TextField()
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    views = models.ManyToManyField(Ip, related_name='post_views', blank=True)

    class Meta:
        ordering = ['-pub_date']
        verbose_name_plural = 'Посты'
        verbose_name = 'Пост'

    def __str__(self) -> str:
        return self.text[:15]

    def total_views(self):
        return self.views.count()


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             related_name='comments',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(User,
                               related_name='comments',
                               on_delete=models.CASCADE
                               )
    text = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(User,
                             related_name='follower',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(User,
                               related_name='following',
                               on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=('user', 'author'),
                                    name='unique_list'),
            models.CheckConstraint(
                check=~Q(user=F('author')), name='author'
            )
        ]
