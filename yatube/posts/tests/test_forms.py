import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from ..forms import PostForm
from ..models import Comment, Post
from django.test import Client, TestCase, override_settings
from django.urls import reverse

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.form = PostForm()

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

    def test_create_post_for_authorized_client(self):
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, (
            reverse('posts:profile', kwargs={'username': 'HasNoName'})
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                image='posts/small.gif',
            ).exists()
        )

    def test_create_post_for_guest(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        redirect = (
            reverse('users:login') + '?next=' + reverse('posts:post_create')
        )
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_edit_post_for_author(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Изменённый текст',
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': posts_count}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, (
            reverse('posts:post_detail', kwargs={'post_id': posts_count})
        ))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                id=posts_count,
                image='posts/small2.gif',
            ).exists()
        )

    def test_edit_post_for_guest(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Изменённый текст',
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': posts_count}),
            data=form_data,
            follow=True
        )
        redirect = (
            reverse('users:login') + '?next='
            + reverse('posts:post_edit', kwargs={'post_id': posts_count})
        )
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
                id=posts_count
            ).exists()
        )

    def test_add_comment_for_guest(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст комментария',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': posts_count}),
            data=form_data,
            follow=True
        )
        redirect = (
            reverse('users:login') + '?next='
            + reverse('posts:add_comment', kwargs={'post_id': posts_count})
        )
        self.assertRedirects(response, redirect)

    def test_add_comment_for_authorized_client(self):
        posts_count = Post.objects.count()
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': posts_count}),
            data=form_data,
            follow=True
        )
        redirect = (
            reverse('posts:post_detail', kwargs={'post_id': posts_count})
        )
        self.assertRedirects(response, redirect)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                id=comment_count + 1
            ).exists()
        )
