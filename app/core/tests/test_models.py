"""
Tests for models
"""

from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_user(email="user@test.com", password="testpass123"):
    """Create and return a new user"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Test models"""

    def test_create_user_with_email_successful(self):
        """Test creating a user with email is successful"""
        email = "test@example.com"
        password = "testpass123"

        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users"""
        sample_emails = [
            ("test1@EXAMPLE.com", "test1@example.com"),
            ("Test2@Example.com", "Test2@example.com"),
            ("TEST3@EXAMPLE.COM", "TEST3@example.com"),
            ("test4@example.COM", "test4@example.com"),
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, "pass123")
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test create a new user without email raises value error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "pass123")

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = get_user_model().objects.create_superuser(
            "test@example.com",
            "pass123",
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creatiing a recipe is successful"""
        user = get_user_model().objects.create_superuser(
            "test@example.com",
            "pass123",
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title="Sample Recipe",
            duration=300,
            price=Decimal("5.50"),
            description="this is a sample recipe",
        )
        self.assertEqual(recipe.title, str(recipe))

    def test_create_tag(self):
        """Test creating a tag is successful"""
        user = create_user()
        tag = models.Tag.objects.create(name="Tag1", user=user)

        self.assertEqual(tag.name, str(tag))

    def test_create_ingredient(self):
        """Test creating an ingredient is successful."""
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name="Ingredient1",
        )

        self.assertEqual(str(ingredient), ingredient.name)
