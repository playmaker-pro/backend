from django.test import TestCase
from rest_framework.test import APIClient


class RolesAPITest(TestCase):
    def test_get_roles(self):
        client = APIClient()
        response = client.get('/api/roles/')
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {'roles': ['admin', 'manager', 'employee']})
