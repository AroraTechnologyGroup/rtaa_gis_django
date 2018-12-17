#!/usr/bin/env python
import django
from django.conf import settings
from django.test.utils import get_runner
import os, sys

if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.test_settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    test1 = test_runner.run_tests(["fileApp.tests"])
    test2 = test_runner.run_tests(["lpm.tests"])
    test3 = test_runner.run_tests(["cloudSync.tests"])
    result = list({test1, test2, test3})
    sys.exit(sum(result))
