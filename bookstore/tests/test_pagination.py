from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from order.models import Order
from product.models import Category, Product

PAGE_SIZE = 5


class PaginationTest(APITestCase):
    """A paginação do DRF vale para todos os ViewSets (5 itens por página)."""

    def setUp(self):
        for i in range(12):
            Category.objects.create(title=f"Categoria {i}", slug=f"categoria-{i}")
            Product.objects.create(title=f"Livro {i}", price=10 + i)
        user = User.objects.create_user(username="pedro", password="senha-teste-123")
        product = Product.objects.first()
        for _ in range(7):
            order = Order.objects.create(user=user)
            order.product.set([product])

    def url(self, name):
        return reverse(f"{name}-list", kwargs={"version": "v1"})

    def test_response_has_pagination_keys(self):
        response = self.client.get(self.url("product"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), {"count", "next", "previous", "results"})

    def test_first_page(self):
        response = self.client.get(self.url("product"))
        self.assertEqual(response.data["count"], 12)
        self.assertEqual(len(response.data["results"]), PAGE_SIZE)
        self.assertIsNone(response.data["previous"])
        self.assertIn("page=2", response.data["next"])
        self.assertEqual(response.data["results"][0]["title"], "Livro 0")

    def test_middle_page(self):
        response = self.client.get(self.url("product"), {"page": 2})
        self.assertEqual(len(response.data["results"]), PAGE_SIZE)
        self.assertIsNotNone(response.data["previous"])
        self.assertIn("page=3", response.data["next"])
        self.assertEqual(response.data["results"][0]["title"], "Livro 5")

    def test_last_page(self):
        response = self.client.get(self.url("product"), {"page": 3})
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIsNone(response.data["next"])

    def test_invalid_page_returns_404(self):
        response = self.client.get(self.url("product"), {"page": 99})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_category_is_paginated(self):
        response = self.client.get(self.url("category"))
        self.assertEqual(response.data["count"], 12)
        self.assertEqual(len(response.data["results"]), PAGE_SIZE)

    def test_order_is_paginated(self):
        response = self.client.get(self.url("order"), {"page": 2})
        self.assertEqual(response.data["count"], 7)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIsNone(response.data["next"])
