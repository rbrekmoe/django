import unittest

from django.db import connection
from django.test import TestCase
from django.test.runner import DiscoverRunner
from django.utils import six

from .models import Person


@unittest.skipUnless(connection.vendor == 'sqlite', 'Only run on sqlite so we can check output SQL.')
class TestDebugSQL(unittest.TestCase):

    class PassingTest(TestCase):
        def runTest(self):
            Person.objects.filter(first_name='pass').count()

    class FailingTest(TestCase):
        def runTest(self):
            Person.objects.filter(first_name='fail').count()
            self.fail()

    class ErrorTest(TestCase):
        def runTest(self):
            Person.objects.filter(first_name='error').count()
            raise Exception

    def _test_output(self, verbosity):
        runner = DiscoverRunner(debug_sql=True, verbosity=0)
        suite = runner.test_suite()
        suite.addTest(self.FailingTest())
        suite.addTest(self.ErrorTest())
        suite.addTest(self.PassingTest())
        old_config = runner.setup_databases()
        stream = six.StringIO()
        resultclass = runner.get_resultclass()
        runner.test_runner(
            verbosity=verbosity,
            stream=stream,
            resultclass=resultclass,
        ).run(suite)
        runner.teardown_databases(old_config)

        stream.seek(0)
        return stream.read()

    def test_output_normal(self):
        full_output = self._test_output(1)
        for output in self.expected_outputs:
            self.assertIn(output, full_output)
        for output in self.verbose_expected_outputs:
            self.assertNotIn(output, full_output)

    def test_output_verbose(self):
        full_output = self._test_output(2)
        for output in self.expected_outputs:
            self.assertIn(output, full_output)
        for output in self.verbose_expected_outputs:
            self.assertIn(output, full_output)

    if six.PY3:
        expected_outputs = [
            ('''QUERY = 'SELECT COUNT(%s) AS "__count" '''
                '''FROM "test_runner_person" WHERE '''
                '''"test_runner_person"."first_name" = %s' '''
                '''- PARAMS = ('*', 'error');'''),
            ('''QUERY = 'SELECT COUNT(%s) AS "__count" '''
                '''FROM "test_runner_person" WHERE '''
                '''"test_runner_person"."first_name" = %s' '''
                '''- PARAMS = ('*', 'fail');'''),
        ]
    else:
        expected_outputs = [
            ('''QUERY = u'SELECT COUNT(%s) AS "__count" '''
                '''FROM "test_runner_person" WHERE '''
                '''"test_runner_person"."first_name" = %s' '''
                '''- PARAMS = (u'*', u'error');'''),
            ('''QUERY = u'SELECT COUNT(%s) AS "__count" '''
                '''FROM "test_runner_person" WHERE '''
                '''"test_runner_person"."first_name" = %s' '''
                '''- PARAMS = (u'*', u'fail');'''),
        ]

    verbose_expected_outputs = [
        'runTest (test_runner.test_debug_sql.FailingTest) ... FAIL',
        'runTest (test_runner.test_debug_sql.ErrorTest) ... ERROR',
        'runTest (test_runner.test_debug_sql.PassingTest) ... ok',
    ]
    if six.PY3:
        verbose_expected_outputs += [
            ('''QUERY = 'SELECT COUNT(%s) AS "__count" '''
                '''FROM "test_runner_person" WHERE '''
                '''"test_runner_person"."first_name" = %s' '''
                '''- PARAMS = ('*', 'pass');'''),
        ]
    else:
        verbose_expected_outputs += [
            ('''QUERY = u'SELECT COUNT(%s) AS "__count" '''
                '''FROM "test_runner_person" WHERE '''
                '''"test_runner_person"."first_name" = %s' '''
                '''- PARAMS = (u'*', u'pass');'''),
        ]
