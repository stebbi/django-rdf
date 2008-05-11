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

