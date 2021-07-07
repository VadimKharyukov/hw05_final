from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser',
                                            password=111111111)
        cls.text = 'Тестовый текст'
        cls.post = Post.objects.create(text=cls.text, author=cls.user)
        cls.group = Group.objects.create(title='testgroup', slug='slug')

    def test_group_title(self):
        test_title = self.group.title
        self.assertEqual(test_title, str(self.group))

    def test_post_text(self):
        test_text = self.post.text
        self.assertEqual(test_text, str(self.post))
