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
