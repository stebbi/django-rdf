from django.conf.urls.defaults import patterns

from rdf.views import resources, sparql

ONTOLOGY_CODE = '(?P<ontology_code>[\w-]+)'
CONCEPT_NAME = '(?P<concept_name>[\w]+)'

urlpatterns = patterns('',
    (r'^sparql/$', sparql),
    (r'^resources/' + ONTOLOGY_CODE + '/' + CONCEPT_NAME + '/$', resources),
)

