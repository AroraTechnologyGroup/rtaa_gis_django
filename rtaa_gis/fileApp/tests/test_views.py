from rest_framework.test import APIRequestFactory
from rest_framework.test import APITestCase
from django.core.urlresolvers import reverse


class TestAssignmentViewSet(APITestCase):
    def test_get(self):
        response = self.client.get('/fileApp/eng-assignments/')
        self.assertEqual(response.status_code, 200)

    def test__clean(self):
        pass


class TestFileViewSet(APITestCase):
    def test_get(self):
        response = self.client.get('/fileApp/eng-files/')
        self.assertEqual(response.status_code, 200)


class TestGridViewSet(APITestCase):
    def test_get(self):
        response = self.client.get('/fileApp/grids/')
        self.assertEqual(response.status_code, 200)


# class TestIOViewSet(APITestCase):
#     def test__download(self):
#         self.fail()
#
#     def test__upload(self):
#         self.fail()
#
#
# class TestPagedFileViewSet(APITestCase):
#     def test__view(self):
#         self.fail()
#
#     def test__build(self):
#         self.fail()
#
#     def test__delete(self):
#         self.fail()
#
#     def test__grids(self):
#         self.fail()
#
#     def test__clean(self):
#         self.fail()
#
#     def test__stop_monitors(self):
#         self.fail()
#
#     def test__start_monitors(self):
#         self.fail()
