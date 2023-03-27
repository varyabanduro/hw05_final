import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Comment, Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            post=cls.post,
            author=cls.author,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)
        cache.clear()

    def test_pages_uses_correct_template_for_author(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'HasNoName'}):
                ('posts/profile.html'),
            reverse('posts:post_detail', kwargs={'post_id': '1'}):
                ('posts/post_detail.html'),
            reverse('posts:post_edit', kwargs={'post_id': '1'}):
                ('posts/create_post.html'),
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_uses_correct_template_for_guest(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'HasNoName'}):
                ('posts/profile.html'),
            reverse('posts:post_detail', kwargs={'post_id': '1'}):
                ('posts/post_detail.html'),
            reverse('posts:post_edit', kwargs={'post_id': '1'}):
                ('users/login.html'),
            reverse('posts:post_create'): 'users/login.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name, follow=True)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        post_list = response.context['page_obj'][0]
        text = post_list.text
        image = post_list.image
        self.assertEqual(text, self.post.text)
        self.assertEqual(image, self.post.image)

    def test_group_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        post_list = response.context['page_obj'][0]
        group_post = response.context['groups']
        text = post_list.text
        group_title = group_post.title
        image = post_list.image
        self.assertEqual(text, self.post.text)
        self.assertEqual(group_title, self.group.title)
        self.assertEqual(image, self.post.image)

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        post_list = response.context['page_obj'][0]
        post_author = post_list.author
        text = post_list.text
        image = post_list.image
        self.assertEqual(text, self.post.text)
        self.assertEqual(post_author, self.author)
        self.assertEqual(image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        post = response.context['post']
        post_author = post.author
        text = post.text
        post_id = post.pk
        image = post.image
        comment = response.context['comments'][0]
        post_comment = comment.text
        self.assertEqual(text, self.post.text)
        self.assertEqual(post_author, self.author)
        self.assertEqual(post_id, self.post.pk)
        self.assertEqual(image, self.post.image)
        self.assertEqual(post_comment, self.comment.text)

    def test_post_edit_show_correct_context(self):
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_with_group_page_show_correct_context(self):
        reverse_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'})
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post_list = response.context['page_obj'][0]
                post_text = post_list.text
                post_author = post_list.author
                post_group = post_list.group.title
                self.assertEqual(post_text, self.post.text)
                self.assertEqual(post_author, self.author)
                self.assertEqual(post_group, self.group.title)

    def test_page_404_uses_correct_template(self):
        reverse_name = 'page_not_found'
        template = 'core/404.html'
        response = self.guest_client.get(reverse_name, follow=True)
        self.assertTemplateUsed(response, template)

    def test_cache_index(self):
        first_response = self.authorized_client.get(reverse('posts:index'))
        Post.objects.filter(pk=1).delete()
        second_response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_response.content, second_response.content)
        cache.clear()
        third_response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(second_response.content, third_response.content)

    def test_follow_index(self):
        self.follow_client = User.objects.create_user(username='Varya')
        self.not_follow_client = Client()
        self.not_follow_client.force_login(self.follow_client)
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'auth'})
        )
        reverse_name = reverse('posts:follow_index')
        response = self.authorized_client.get(reverse_name)
        resp_not_follow_client = self.not_follow_client.get(reverse_name)
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(len(resp_not_follow_client.context['page_obj']), 0)
        Post.objects.create(
            author=self.author,
            text='Тестовый пост',
        )
        response = self.authorized_client.get(reverse_name)
        resp_not_follow_client = self.not_follow_client.get(reverse_name)
        self.assertEqual(len(response.context['page_obj']), 2)
        self.assertEqual(len(resp_not_follow_client.context['page_obj']), 0)

    def test_authorized_client_follow_someone(self):
        follow_count_first = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'auth'})
        )
        self.assertEqual(follow_count_first + 1, Follow.objects.count())
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': 'auth'})
        )
        self.assertEqual(follow_count_first, Follow.objects.count())

        

