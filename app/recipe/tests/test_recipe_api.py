"""
Tests for recipe API
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from core.models import Recipe, Tag

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """create and return a recipe detail url"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        "title": "Jellof rice recipe",
        "duration": 1800,
        "price": Decimal("10.5"),
        "description": "Jellof rice is a perfect sample recipe",
        "link": "http://example.com/jellofrecipe.pdf",
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """Create and return new user"""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated Recipe API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to test API"""
        res = self.client.get(RECIPES_URL)
        # print('res is', str(res))
        self.assertEqual(res.status_code, HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated Recipe API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="user@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_all_recipes(self):
        """Test get a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_user_recipes_(self):
        """Test get a list of recipes limited to the auth user"""
        other_user = create_user(
            email="otheruser@test.com",
            password="testpass123",
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user).order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get details of a recipe"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe"""
        payload = {
            "title": "Sample recipe",
            "duration": 1200,
            "price": Decimal("5.99"),
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """Test partial update of a created recipe"""
        original_link = "https://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title="Sample recipe title",
            link=original_link,
        )
        payload = {"title": "New recipe title"}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        """Test full update of a created recipe"""
        recipe = create_recipe(
            user=self.user,
            title="Sample recipe title",
            description="Sample recipe decscription",
            link="https://example.com/recipe.pdf",
        )
        payload = {
            "title": "New recipe title",
            "description": "New recipe description",
            "duration": 1200,
            "price": Decimal("2.45"),
            "link": "https://example.com/new-recipe.pdf",
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the recipe user returns error"""
        new_user = create_user(
            email="newuser@test.com",
            password="testpass123",
        )
        recipe = create_recipe(user=self.user)
        payload = {"user": new_user.id}

        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe is successful"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe(self):
        """Test deleting another user's recipe is unsuccessful"""
        new_user = create_user(
            email="newuser@test.com",
            password="testpass123",
        )
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating a new recipe using a new tag"""

        payload = {
            "title": "Thai prawn curry",
            "duration": 3600,
            "price": Decimal("12.5"),
            "tags": [
                {"name": "Thai"},
                {"name": "Dinner"},
            ],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            exists = recipe.tags.filter(name=tag["name"], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a new recipe with an existing tag"""

        # WHEN
        indian_tag = Tag.objects.create(
            name="Indian",
            user=self.user,
        )
        payload = {
            "title": "Indian tikki masala",
            "duration": 3600,
            "price": Decimal("12.5"),
            "tags": [
                {"name": "Indian"},
                {"name": "Dinner"},
            ],
        }

        # THEN
        res = self.client.post(RECIPES_URL, payload, format="json")

        # EXPECT
        self.assertEqual(res.status_code, HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        self.assertIn(indian_tag, recipe.tags.all())

        for tag in payload["tags"]:
            exists = recipe.tags.filter(name=tag["name"], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating a tag during recipe update"""

        # WHEN
        recipe = create_recipe(user=self.user)

        # THEN
        payload = {"tags": [{"name": "Lunch"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        # EXPECT
        self.assertEqual(res.status_code, HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user,name="Lunch")
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating an existing recipe"""

        # WHEN
        tag_breakfast = Tag.objects.create(name="Breakfast", user=self.user)
        tag_lunch = Tag.objects.create(name="Lunch", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        # THEN
        payload = {"tags": [{"name": "Lunch"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        # EXPECT
        self.assertEqual(res.status_code, HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing a recipes tags"""

        # WHEN
        tag_dessert = Tag.objects.create(name="Dessert", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_dessert)

        # THEN
        payload = {"tags": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        # EXPECT
        self.assertEqual(res.status_code, HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
