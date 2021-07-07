from django.test import Client, TestCase
from http import HTTPStatus


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.templates_pages_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }

    def test_about_url_exists_at_desired_location(self):
        for template, pathname in self.templates_pages_names.items():
            with self.subTest(pathname=pathname):
                response = self.guest_client.get(pathname)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_url_uses_correct_template(self):
        for template, pathname in self.templates_pages_names.items():
            with self.subTest(template=template, pathname=pathname):
                response = self.guest_client.get(pathname)
                self.assertTemplateUsed(response, template)
