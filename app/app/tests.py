"""
Sample tests
"""

from django.test import SimpleTestCase
from app import calc


class CalcTests(SimpleTestCase):
    """Test the calc module"""

    def test_add_numbers(self):
        """Test adding numbers correctly"""
        res = calc.add(5, 6)

        self.assertEqual(res, 11)

    def test_subtract(self):
        """Test subtracting numbers"""
        res = calc.subtract(5, 9)

        self.assertEqual(res, 4)
