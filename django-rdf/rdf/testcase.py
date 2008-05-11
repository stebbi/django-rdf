from django.core.management import call_command
from django.test.testcases import TestCase as DjangoTestCase

class TestCase(DjangoTestCase):

    def setUp(self):
        call_command('syncvb', verbosity=0)   # Set up, synthesize and install ontology
