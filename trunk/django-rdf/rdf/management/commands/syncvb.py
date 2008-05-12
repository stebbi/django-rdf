import os, sys, traceback
from optparse import make_option

from django.conf import settings
from django.core import serializers
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection, transaction
from django.db.models import get_app, get_apps

from rdf import magic


try:
    set # IGNORE:W0104
except NameError:
    from sets import Set as set   # Python 2.3 fallback


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
    )

    help = 'Installs the named ontology in the database.'
    args = "ontology [ontology ...]"

    def __init__(self):
        BaseCommand.__init__(self)
        self.style = no_style()
        # Keep a count of the installed objects and ontologies
        self.count = [0, 0]
        self.models = set()
        self.verbosity, self.show_traceback, self.fail_gracefully = 1, False, False

    def handle(self, *labels, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.show_traceback = options.get('traceback', False)
        self.fail_gracefully = options.get('graceful', False)
        
        if not hasattr(settings, 'SERIALIZATION_MODULES') \
            or not settings.SERIALIZATION_MODULES.has_key('rdfxml') \
            or not settings.SERIALIZATION_MODULES.has_key('xsd'):
            print \
'''Your project needs to be configured with serializers for the RDF/XML and XSD 
formats. Add the following lines at the bottom of your settings.py to fix this:

    SERIALIZATION_MODULES = {
        'rdfxml': 'rdf.serializers.rdfxml',
        'xsd': 'rdf.serializers.xsd',
    }
'''
            return
        
        self.cursor = connection.cursor()
        transaction.commit_unless_managed()
        transaction.enter_transaction_management()
        transaction.managed(True)
        try: 
            # Make sure the RDF core app is handled before everything else
            rdf = get_app('rdf')
            if 1 > len(labels) or 'magic' in labels:
                magic.pre()
                paths = [os.path.join(os.path.dirname(rdf.__file__), 'ontology')]
                self._handle_fragments(labels, paths) # IGNORE:W0142
                magic.post()
            # Next mirror Django models to create additional fragments
            call_command('mirror', verbosity=self.verbosity)
            # Now handle the remaining ontology fragments, included the mirrored ones
            labels = [l for l in labels if 'rdf' != l]
            paths = [os.path.join(os.path.dirname(app.__file__), 'ontology') \
                for app in get_apps() if not app is rdf]
            self._handle_fragments(labels, paths) 
            magic.compiler_support()
            magic.predicate_spans() 
            # Done - clean up and exit
            if self.count[0] > 0:
                sequence_sql = connection.ops.sequence_reset_sql(self.style, self.models)
                if sequence_sql:
                    if 1 < self.verbosity:
                        print "Resetting sequences"
                    for line in sequence_sql:
                        self.cursor.execute(line)
            transaction.commit()
        except Exception, x: # IGNORE:W0703 Catching everything
            transaction.rollback()
            print 'Ontology synchronization failed with an exception.'
            exc = sys.exc_info()
            print x, type(x)
            traceback.print_tb(exc[2])
        self.cursor.close()
        transaction.leave_transaction_management()
        if 0 < self.verbosity:
            print "No new ontology elements installed." if 0 == self.count[0] else \
                "Inserted or updated %d objects from %d ontology fragments" \
                % tuple(self.count)
            
    def _handle_fragments(self, labels, paths): # IGNORE:W0142
        dirs = [dir for dir in paths if os.path.isdir(dir)]
        fragments = [(dir, os.listdir(dir)) for dir in dirs]
        for dir, filenames in fragments:
            if not filenames:
                continue
            for filename in filenames:
                parts = filename.split('.')
                label, format = '.'.join(parts[:-1]), parts[-1]
                if 0 < len(labels) and not label in labels:
                    if 1 < self.verbosity:
                        print 'Skipping %s' % label
                    continue
                if format in serializers.get_public_serializer_formats():
                    self._handle_fragment(dir, label, format)
                elif 0 < self.verbosity:
                    print 'Unrecognized serialization format `%s` (%s in %s)' \
                        % (format, label, dir)

    def _handle_fragment(self, dir, label, format):
        path = os.path.join(dir, '.'.join([label, format]))
        if 0 < self.verbosity:
            print 'Loading `%s` from %s' % (label, path)
        self.count[1] += 1
        s = serializers.deserialize(format, path)
        s.verbosity, s.traceback, s.graceful = \
            self.verbosity, self.show_traceback, self.fail_gracefully
        for o in s:
            self.count[0] += 1
            self.models.add(o.__class__)
            o.save()
            if 1 < self.verbosity:
                print 'Deserialized', type(o), o

# Copyright (c) 2008, Stefan B Sigurdsson
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 
#     1. Redistributions of source code must retain the above copyright notice, 
#        this list of conditions and the following disclaimer.
#     
#     2. Redistributions in binary form must reproduce the above copyright 
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
# 
#     3. Neither the name of Django nor the names of its contributors may be used
#        to endorse or promote products derived from this software without
#        specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
