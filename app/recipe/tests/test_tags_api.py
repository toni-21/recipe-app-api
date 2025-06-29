from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer

TAGS_URL = reverse("recipe:tag-list")


def detail_url(tag_id):
    """Create and return a tag detail url"""
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email="user@test.com", password="testpass123"):
    """Create and return a new user"""
    return get_user_model().objects.create_user(email, password)


class PublicTagAPITests(TestCase):
    """Test unauthenticated Tag API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to test API"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagAPITests(TestCase):
    """Test authenticated Tag API requests"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrive_tags(self):
        """Test retreiving a list of tags"""
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Halal")

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated user"""
        user2 = create_user(email="user2@test.com")
        Tag.objects.create(user=user2, name="Fruity")
        tag = Tag.objects.create(user=self.user, name="Veggies")

        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tag(self):
        """Test updating a tag"""
        tag = Tag.objects.create(user=self.user, name="After Dinner")

        payload = {"name": "Dessert"}
        url = detail_url(tag_id=tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        """Test deleting a tag"""
        tag = Tag.objects.create(user=self.user, name="Lunch")

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(user=self.user).exists())
