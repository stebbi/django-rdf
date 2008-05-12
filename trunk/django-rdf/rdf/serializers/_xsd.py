import sys, traceback

from ..models import Namespace, Ontology, Resource, Concept
from ..serializers import _DXML, _JC, _split_URI
from ..shortcuts import get


XS, RDF, RDFS = get((Namespace, 'xs'), (Namespace, 'rdf'), (Namespace, 'rdfs'))

LITERAL = RDFS['Literal']

TARGETNAMESPACE = 'targetNamespace'
XS_SCHEMA = _JC(XS.uri, 'schema')
XS_SIMPLETYPE = _JC(XS.uri, 'simpleType')
XS_COMPLEXTYPE = _JC(XS.uri, 'complexType')
XS_RESTRICTION = _JC(XS.uri, 'restriction')


class _Deserializer(_DXML):
    
    def __init__(self, ontology_path, **options):
        _DXML.__init__(self, # IGNORE:W0142
            ontology_path, 
            {XS_SCHEMA: self._xs_schema,
             XS_SIMPLETYPE: self._xs_simpletype,},
            **options)
        self._ontology = None
        self._bases = []

    def _postiter_hook(self):
        for t, bns, bname in self._bases:
            try: 
                b = Concept.objects.get(resource__namespace=bns, resource__name=bname)
                t.bases.add(b)
                t.save()
            except Concept.DoesNotExist, x:
                self._except(Concept.DoesNotExist, x, '%s %s' % (bns, bname))

    def _xs_schema(self, e):
        ns_uri = e.get(TARGETNAMESPACE)
        namespace = Namespace.objects.get(resource__name=ns_uri)
        title, description = ns_uri, ns_uri
        match = Ontology.objects.filter(resource=namespace.resource)
        ontology = None
        if 1 > match.count():
            ontology = Ontology(
                resource=namespace.resource,
                title=title,
                description=description)
            yield ontology
        else:
            ontology = match[0]
        self._ontology = ontology

    def _xs_simpletype(self, e):
        name = e.get('name')
        ns = self._ontology.namespace
        match = Concept.objects.filter(resource__namespace=ns, resource__name=name)
        t = None
        if 0 <  match.count():
            t = match[0]
            t.resource.type = LITERAL
            yield t.resource
            t.model_name = 'rdf.models.String'
            t.literal = True
        else:
            r = Resource(
                namespace=ns, 
                name=name, 
                type=LITERAL)
            yield r
            t = Concept(
                resource=r,
                title=name.title(), 
                description='...', 
                model_name='rdf.models.String',
                literal=True)
        yield t
        r = e.find(XS_RESTRICTION)
        r = r.get('base') if r else None
        if r is not None:
            bns, bname = _split_URI(r)
            if not (XS == bns and 'anySimpleType' == bname):
                self._bases.append((t, bns, bname))


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
