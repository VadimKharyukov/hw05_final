from django import forms
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from http import HTTPStatus

from ..models import Follow, Group, Post, User


class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.text = 'Тестовый текст'
        cls.group = Group.objects.create(title='testgroup',
                                         slug='slug')
        cls.post = Post.objects.create(text=cls.text,
                                       author=cls.user,
                                       group=cls.group)
        cls.templates_pages_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group', kwargs={
                'slug': cls.group.slug}),
            'posts/new_post.html': reverse('new_post')
        }

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_template(self):
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_first_page_context_shows_correctly(self):
        response = self.authorized_client.get(reverse('index'))
        posts_0 = response.context['page'][0]
        self.assertEqual(posts_0, self.post)

    def test_group_page_context_shows_correctly(self):
        response = self.authorized_client.get(reverse('group', kwargs={
            'slug': self.group.slug}))
        group_0 = response.context['group']
        posts_0 = response.context['page'][0]
        self.assertEqual(group_0, self.group)
        self.assertEqual(posts_0, self.post)

    def test_new_page_context_shows_correct(self):
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_context_page_post_edit(self):
        response = self.authorized_client.get(reverse('edit_post', kwargs={
            'username': self.user.username,
            'post_id': self.post.id
        }))
        from_fields = {
            'text': forms.fields.CharField
        }
        for value, expected in from_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_context_page_profile(self):
        response = self.authorized_client.get(reverse('profile', kwargs={
            'username': self.user.username
        }))
        profile = {
            'author': self.post.author,
            'post_count': self.user.posts.count()
        }
        for value, expected in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expected)
        test_page = response.context['page'][0]
        self.assertEqual(test_page, self.user.posts.all()[0])

    def test_context_page_post(self):
        response = self.authorized_client.get(reverse('post', kwargs={
            'username': self.user.username,
            'post_id': self.post.id
        }))
        profile = {
            'author': self.post.author,
            'post': self.post
        }
        for value, expected in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expected)

    def test_created_post_related_own_page(self):
        response = self.authorized_client.get(reverse('index'))
        first_object = response.context['page'][0]
        object_group = first_object.group
        self.assertEqual(object_group, self.group)


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.text = 'Тестовый текст'
        cls.group = Group.objects.create(title='testgroup',
                                         slug='slug')
        cls.client = Client()
        cls.client.force_login(cls.user)
        cls.templates_pages_names = (
            reverse('index'),
            reverse('group', kwargs={'slug': cls.group.slug}),
            reverse('profile', kwargs={
                'username': cls.user.username}))

        for i in range(13):
            cls.post = Post.objects.create(
                text='текст {i}', author=cls.user, group=cls.group)

    def test_first_page_contains_correctly_posts(self):
        cache.clear()
        for pathname in self.templates_pages_names:
            with self.subTest():
                response = self.client.get(pathname)
                self.assertEqual(len(response.context.get(
                    'page').object_list), 10)

    def test_second_page_contains_correctly_posts(self):
        for pathname in self.templates_pages_names:
            with self.subTest():
                response = self.client.get(pathname + '?page=2')
                self.assertEqual(len(response.context.get(
                    'page').object_list), 3)


class TestCache(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.authorized_user = Client()
        cls.authorized_user.force_login(cls.user)
        cls.group = Group.objects.create(title='TestGroup',
                                         slug='test_slug',
                                         description='Test description')

    def cache_index(self):
        cache.clear()
        Post.objects.create(
            text='test text',
            author=self.user
        )
        self.authorized_user.get(reverse('index'))
        response = self.authorized_user.get(reverse('index'))
        self.assertEqual(response.context, None)
        cache.clear()
        response = self.authorized_user.get(reverse('index'))
        self.assertNotEqual(response.context, None)
        self.assertEqual(response.context['page'][0].text, 'test text')


class TestFollow(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(title='testgroup',
                                         slug='slug',
                                         description='description')
        cls.follow_user = User.objects.create_user(username='testauthor')
        cls.text = 'Тестовый текст'

    def setUp(self):
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

    def test_authorized_user_can_subscribe(self):
        response = self.authorized_user.post(
            reverse('profile_follow', args=(self.follow_user,)), follow=True)

        is_follow = Follow.objects.filter(user=self.user,
                                          author=self.follow_user).count()
        self.assertEqual(is_follow, 1)
        self.assertIn("Отписаться", response.content.decode())

    def test_authorized_user_can_unsubscribe(self):
        Follow.objects.create(user=self.user, author=self.follow_user)
        is_follow = Follow.objects.filter(user=self.user,
                                          author=self.follow_user).count()
        self.assertEqual(is_follow, 1)
        response = self.authorized_user.post(
            reverse('profile_unfollow',
                    args=(self.follow_user,)), follow=True)
        self.assertIn("Подписаться", response.content.decode())

        is_unfollow = Follow.objects.filter(user=self.user,
                                            author=self.follow_user).count()
        self.assertEqual(is_unfollow, 0)

    def test_new_post_add_in_follow_index(self):
        self.post_follow = Post.objects.create(
            text=self.text,
            author=self.follow_user
        )
        self.follow = Follow.objects.create(
            user=self.user, author=self.follow_user
        )
        follow_index = self.authorized_user.get(reverse(
            'follow_index'))
        self.assertIn(self.text,
                      follow_index.content.decode())

    def test_not_follow_post_dont_appears_in_follow_index(self):
        self.post_follow = Post.objects.create(
            text=self.text,
            author=self.user
        )
        follow_index = self.authorized_user.get(reverse(
            'follow_index'))
        self.assertNotIn(self.text,
                         follow_index.content.decode())


class TestComments(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.comment_user = User.objects.create_user(username='testcommentuser')
        cls.text = 'Тестовый текст'
        cls.post = Post.objects.create(text=cls.text, author=cls.user)
        cls.url_comment = reverse('add_comment', kwargs={
            'username': cls.post.author.username, 'post_id': cls.post.id})

    def setUp(self):
        self.anonim = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.comment_user)

    def test_auth_user_can_comment_post(self):
        response = self.authorized_user.post(self.url_comment, {
            'text': 'test comment'}, follow=True)
        self.assertContains(response, 'test comment')

    def test_unauthorized_user_cant_comment_post(self):
        response = self.anonim.post(self.url_comment, {
            'text': self.text},)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
