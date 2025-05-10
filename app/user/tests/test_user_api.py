"""
Tests for the user API
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")


def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the public features of the user API"""

    def setUp(self):
        self.client = APIClient()
        return super().setUp()

    def test_create_user_success(self):
        """test creating user is successsful"""
        payload = {
            "email": "test@example.com",
            "name": "Test Name",
            "password": "testpass123",
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))

        self.assertNotIn("password", res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists"""
        payload = {
            "email": "test@example.com",
            "name": "Test Name",
            "password": "testpass123",
        }

        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test error returned if password is less than 5 chars"""
        payload = {
            "email": "shortt@example.com",
            "name": "Test Name",
            "password": "tw",
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        use_objects = get_user_model().objects
        user_exists = use_objects.filter(email=payload["email"]).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token for vaild credentials"""

        user_details = {
            "email": "test@example.com",
            "name": "Test Name",
            "password": "test-password-123",
        }

        create_user(**user_details)

        payload = {
            "email": user_details["email"],
            "password": user_details["password"],
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentails(self):
        """Test return error if credentials are invalid"""
        create_user(email="test@example.com", password="goodpass")

        payload = {
            "email": "test@example.com",
            "password": "badpass",
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting blank password return an error"""
        payload = {
            "email": "test@example.com",
            "password": "",
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
