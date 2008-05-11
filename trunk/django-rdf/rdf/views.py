from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from rdf.models import Concept, Namespace, Ontology
from rdf.query.query import SPARQLQuerySet
from rdf.shortcuts import render_as_rdf, render_to_response


@login_required
def sparql(request):
    """
    Returns the results of the SPARQL query in the `sparql` POST parameter, formatted 
    as RDF/XML.
    """
    offset = int(request['offset']) if request.has_key('offset') else 0
    limit = int(request['limit']) if request.has_key('limit') else 100
    sparql = request['sparql']
    qs = SPARQLQuerySet().sparql(sparql)
    return render_as_rdf(
        resources=qs[offset:limit], count=qs.count(), limit=limit, offset=offset)
    

@login_required
def resources(request, ontology_code, concept_name):
    """
    Returns resources for the given concept in RDF/XML format.
    """
    offset = int(request['offset']) if request.has_key('offset') else 0
    limit = int(request['limit']) if request.has_key('limit') else 100
    c = get_object_or_404(
        Concept, 
        resource__name=concept_name, 
        resource__namespace__code=ontology_code)
    qs = Concept.objects.values_for_concept(concept=c)
    return render_as_rdf(
        resources=qs[offset:limit], offset=offset, limit=limit, count=qs.count())
