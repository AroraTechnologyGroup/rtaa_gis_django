from django.test import TestCase
from lpm.models import Agreement
import os

# setting this environment variable allows fixtures to be loaded
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fixtures/json'))


class TestAgreement(TestCase):
    fixtures = ['agreement', 'space']

    def test_list(self):
        _files = Agreement.objects.all()
        self.assertTrue(_files)
        pass

    def test_filter(self):
        id = 1129
        _agreement = Agreement.objects.filter(id=id)
        self.assertIsInstance(_agreement[0], Agreement)
        pass
