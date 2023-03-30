from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Follow, Group, Post

User = get_user_model()

POST_CUT: int = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки среза текста поста',
        )
        cls.comment = Comment.objects.create(
            text='Комментарий',
            post=cls.post,
            author=cls.user,
        )

    def test_models_have_title(self):
        group = PostModelTest.group
        expected_group_title = group.title
        self.assertEqual(expected_group_title, str(group))

    def test_models_have_text(self):
        post = PostModelTest.post
        expected_post_text = post.text[:POST_CUT]
        self.assertEqual(expected_post_text, str(post))

    def test_models_have_comment(self):
        comment = PostModelTest.comment
        expected_comment_text = comment.text
        self.assertEqual(expected_comment_text, str(comment))

    def test_models_have_following(self):
        following_count = Follow.objects.count()
        author = User.objects.create_user(username='author')
        user = PostModelTest.user
        Follow.objects.create(user=user, author=author)
        expected_following_count = following_count + 1
        self.assertEqual(Follow.objects.count(), expected_following_count)
