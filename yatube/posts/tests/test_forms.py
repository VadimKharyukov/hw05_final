import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache

from ..models import Group, Post, User

TEMP_MEDIA = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='testuser')
        cls.text = 'Тестовый текст'
        cls.post = Post.objects.create(text=cls.text, author=cls.user_author)
        cls.group = Group.objects.create(title='testgroup', slug='slug')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_author)

    def test_posts_form(self):
        post_count = Post.objects.count()
        form_data = {
            'text': self.text,
            'group': self.group.id,
            'image': self.image
        }
        self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        cache.clear()
        self.authorized_client.post(reverse('new_post'), data=form_data)
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(text=form_data['text'],
                                            group=form_data['group'],
                                            image='posts/small.gif').exists())
        self.assertTrue(
            response.context['page'][0].image.name, self.image.name)

    def test_edit_post(self):
        form_data = {
            'text': 'Текст из формы вариация 2',
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse('edit_post', kwargs={
                'username': self.user_author.username, 'post_id': self.post.id
            }), data=form_data)
        response = self.authorized_client.get(reverse('post', kwargs={
            'username': self.user_author.username,
            'post_id': self.post.id}))
        self.assertEqual(response.context['post'].text,
                         form_data['text'])
        self.assertTrue(Post.objects.filter(text=form_data['text'],
                                            id=self.post.id,
                                            group=self.group).exists())
