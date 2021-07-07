from django.urls import reverse
from django.test import Client, TestCase
from django.core.cache import cache
from http import HTTPStatus

from ..models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='testuser')
        cls.non_author = User.objects.create_user(username='non_testuser')
        cls.text = 'Тестовый текст'
        cls.post = Post.objects.create(text=cls.text,
                                       author=cls.author)
        cls.group = Group.objects.create(title='testgroup',
                                         slug='slug')
        cls.templates_url_names = {
            'index.html': '/',
            'group.html': f'/group/{cls.group.slug}/',
            'posts/new_post.html': '/new/',
            'posts/profile.html': f'/{cls.author.username}/',
            'posts/post.html': f'/{cls.author.username}/{cls.post.id}/'}

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_non_author = Client()
        self.authorized_non_author.force_login(self.non_author)

    def test_valid_url_authorized(self):
        for templates, pathname in self.templates_url_names.items():
            with self.subTest(pathname=pathname):
                response = self.authorized_client.get(pathname)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_client.get(
            f'/{self.author.username}/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_valid_url_non_authorized(self):
        for templates, pathname in self.templates_url_names.items():
            with self.subTest(pathname=pathname):
                if pathname == reverse('new_post'):
                    response = self.guest_client.get(pathname)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                else:
                    response = self.guest_client.get(pathname)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.guest_client.get(
            f'/{self.author.username}/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_non_author_urls(self):
        for templates, pathname in self.templates_url_names.items():
            with self.subTest(pathname=pathname):
                response = self.authorized_non_author.get(pathname)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_non_author.get(
            f'/{self.author.username}/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        for template, pathname in self.templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(pathname)
                self.assertTemplateUsed(response, template)
        response = self.authorized_client.get(
            f'/{self.author.username}/{self.post.id}/edit/')
        self.assertTemplateUsed(response, 'posts/new_post.html')

    def test_urls_404_error(self):
        response = self.guest_client.get('/test_404_error/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
