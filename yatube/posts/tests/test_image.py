import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post, User

TEMP_MEDIA = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class TestPostImages(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(title='testgroup',
                                         slug='slug')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')
        cls.text = 'Тестовый текст'
        cls.post = Post.objects.create(author=cls.user,
                                       text=cls.text,
                                       group=cls.group,
                                       image=cls.uploaded)
        cls.url_names = (
            reverse('index'),
            reverse('group', kwargs={
                'slug': cls.group.slug}),
            reverse('post', kwargs={
                'username': cls.user.username, 'post_id': cls.post.id}),
            reverse('profile', kwargs={
                'username': cls.user.username})
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

    def test_image_contains_in_pages(self):
        for pathname in self.url_names:
            with self.subTest(pathname=pathname):
                response = self.authorized_user.get(pathname)
                self.assertContains(response, '<img')
