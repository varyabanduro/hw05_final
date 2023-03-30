from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)
        cache.clear()

    def test_about_url_exists_at_desired_location(self):
        url_names_status_code = {
            '/': HTTPStatus.OK,
            '/group/test-slug/': HTTPStatus.OK,
            '/profile/HasNoName/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/posts/1/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/follow/': HTTPStatus.FOUND,
            '/profile/HasNoName/follow/': HTTPStatus.FOUND,
            '/profile/HasNoName/unfollow/': HTTPStatus.FOUND,
        }
        for url_names, status_code in url_names_status_code.items():
            with self.subTest(status_code=status_code):
                response = self.guest_client.get(url_names)
                self.assertEqual(response.status_code, status_code)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test-slug/',
            'posts/profile.html': '/profile/HasNoName/',
            'posts/post_detail.html': '/posts/1/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                cache.clear()
                self.assertTemplateUsed(response, template)
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_create_post_correct_template(self):
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_edit_post_correct_template(self):
        response = self.author_client.get('/posts/1/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
