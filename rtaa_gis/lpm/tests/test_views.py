from rest_framework.test import APIRequestFactory
from rest_framework.test import APITestCase


class TestAgreementViewSet(APITestCase):
    def test_get(self):
        response = self.client.get('/lpm/agreements/')
        self.assertEqual(response.status_code, 200)


class TestSpaceViewSet(APITestCase):
    def test_get(self):
        response = self.client.get('/lpm/spaces/')
        self.assertEqual(response.status_code, 200)

