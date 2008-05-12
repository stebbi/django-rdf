from rdf.models import \
    Namespace, Predicate, Resource, Concept, Cardinality, CARDINALITIES, _SpanSegment
from rdf.shortcuts import get, get_or_create
from django.db.models.fields import AutoField


def pre():
    '''
    Invoked during the ontology load process, before any ontology definitions 
    are parsed. Establishes the core RDF, RDFS and OWL constructs necessary for 
    successfully parsing RDF ontologies.
    '''

    for d in CARDINALITIES:
        for r in CARDINALITIES:
            Cardinality.objects.get_or_create(domain=d[0], range=r[0])

    # Shortcuts require the RDF, RDFS namespaces and the type and namespace types:
    
    # The resource behind the RDF namespace:
    RDF, _ = Resource.objects.get_or_create(name='http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    
    # The RDF namespace itself: 
    RDF, _ = Namespace.objects.get_or_create(
        code='rdf',
        defaults=dict( 
            resource=RDF,
            title='RDF Vocabulary',
            description='''The RDF vocabulary  published by the W3C as http://www.w3c.org/1999/02/22-rdf-syntax-ns#.'''))
    
    # The resource behind the RDFS namespace: 
    RDFS, _ = Resource.objects.get_or_create(name=u'http://www.w3.org/2000/01/rdf-schema#')
    
    # The RDFS namespace itself: 
    RDFS, _ = Namespace.objects.get_or_create(
        code='rdfs',
        defaults=dict( 
            resource=RDFS,
            title='RDF Schema Vocabulary',
            description='''The RDF Schema vocabulary published by the W3C as http://www.w3.org/2000/01/rdf-schema#.'''))
    
    # The resource behind the namespace type: 
    nsr, _ = Resource.objects.get_or_create(namespace=RDFS, name='Namespace')
    
    # The namespace type: 
    ns, _ = Concept.objects.get_or_create(
        resource=nsr,
        defaults=dict( 
            name='Namespace',
            model_name='rdf.models.Namespace',
            title='RDF Namespace',
            description='The basic RDF namespace concept. All namespaces are examples of this concept.'))
    
    # The resource behind the type type: 
    tr, _ = Resource.objects.get_or_create(namespace=RDFS, name='Class')
    
    # The type itself:
    t, _ = Concept.objects.get_or_create(
        resource=tr,
        defaults=dict( 
            name='Class',
            model_name='rdf.models.Concept',
            title='RDFS Class',
            description='The basic RDFS Class used to form vocabularies.'))
    
    # The resource behind the literal type: 
    lr, _ = Resource.objects.get_or_create(namespace=RDFS, name='Literal')
    
    # The literal itself:
    l, _ = Concept.objects.get_or_create(
        resource=lr,
        defaults=dict(
            model_name='rdf.models.Concept',
            title='RDFS Literal',
            description='The basic RDFS Literal used to form vocabularies.'))
    
    # Assign the namespace type to the namespaces: 
    RDF.resource.type = ns; RDF.resource.save()
    RDFS.resource.type = ns; RDFS.resource.save()
    
    # Assign the type type to the types...:
    tr.type = t; tr.save()
    lr.type = l; lr.save()
    nsr.type = t; nsr.save()
    
    # Shortcuts now work...
    
    get_or_create(
        Concept, RDFS, 'Resource', 
        defaults=dict(
            model_name='rdf.models.Resource',
            title='RDF Resource',
            description='The basic RDF resource concept that all other concepts are derived from.'))
    
    get_or_create(
        (Namespace, 'xml', 'http://www.w3.org/xml/1998/namespace'),
        (Namespace, 'xs', 'http://www.w3.org/2001/XMLSchema#'), # Check out that hash ;)
        (Namespace, 'drdfs', 'http://.../django/schema#'),
        (Namespace, 'owl', 'http://www.w3.org/2002/07/owl#'),
        (Namespace, 'dc', 'http://purl.org/dc/elements/1.1/'))

    get_or_create(
        Concept, RDF, 'Property', 
        defaults=dict(
            model_name='rdf.models.Predicate',
            title='RDF Property',
            description='The RDF property concept. All properties belong to this concept.'))
    
    get_or_create(
        Concept, RDF, 'Statement', 
        defaults=dict(
            model_name='rdf.models.Statement',
            title='RDF Statement',
            description='The RDF statement concept. All statements belong to this concept.'))
    
        
def post():
    '''
    Invoked during the ontology load process, after all core ontology definitions 
    have been parsed but before any additional fragments are loaded. 
    
    Carries out any necessary post-processing for the coreontology elements, 
    including but not limited to: 
    
        * Specifying predicate cardinalities
        * Establishing model mappings for concepts and literals
        * Synthesizing value predicates for literals
        
    '''
    RDF, RDFS, OWL, XS, DC, DRDFS = get(
        (Namespace, 'rdf'), (Namespace, 'rdfs'), (Namespace, 'owl'),
        (Namespace, 'xs'), (Namespace, 'dc'), (Namespace, 'drdfs'))
    
    one_to_one = Cardinality.objects.get(domain='1', range='1')
    any_to_one = Cardinality.objects.get(domain='*', range='1')

    # Ontologies...
    
    ONTOLOGY = OWL['Ontology']
    ONTOLOGY.model_name = 'rdf.models.Ontology'
    ONTOLOGY.save()
    
    _mark_internal_ontologies()
    
    # First arrange support for accessing resource identifier strings, e.g. rdf:about:
    
    URI, _ = get_or_create(
        # URI literal stored in the resources table, in the name field. 
        # This unfortunately leaves off the namespace prefix but will do for now.
        Concept, DRDFS, 'uri', 
        defaults=dict(
            literal=True, 
            model_name='rdf.models.Resource', 
            title='Uniform Resource Identifier', 
            description='A string that uniquely identifies the associated resource.'))
    URI.resource.type = RDFS['Literal']
    URI.resource.save()
        
    get_or_create(
        # Predicate for accessing the URI for a resource.
        Predicate, RDF, 'about', 
        defaults=dict(
            domain=RDFS['Resource'],
            range=URI, 
            cardinality=one_to_one, 
            field_name='rdf.models.Resource.name', # Not quite right... missing prefix
            title='RDF About',
            description='Associates a resource with its URI'))
    
    # Now map some built-in predicates to the right database columns, assign 
    # cardinalities, etc.:

    TYPE = RDF['type']
    TYPE.field_name = 'rdf.models.Resource.type'
    TYPE.cardinality = one_to_one
    TYPE.save()
    
    SUBJECT = RDF['subject']
    SUBJECT.field_name = 'rdf.models.Statement.subject'
    SUBJECT.cardinality = any_to_one
    SUBJECT.save()
    
    PREDICATE = RDF['predicate']
    PREDICATE.field_name = 'rdf.models.Statement.predicate'
    PREDICATE.cardinality = any_to_one
    PREDICATE.save()

    OBJECT = RDF['predicate']
    OBJECT.cardinality = any_to_one
    OBJECT.save()
    
    # RDF['object'] field is more complicated... it is special-cased in the compiler.
    
    b = Concept.objects.get(resource__namespace=XS, resource__name='boolean')
    b.title='Boolean Literal'
    b.description='The literal type used to store Boolean truth values.'
    b.save()
    _recursive_map_model(b, 'rdf.models.Boolean')

    d = Concept.objects.get(resource__namespace=XS, resource__name='date')
    d.title = 'Date Literal'
    d.description = 'The literal type used to store date values.'
    d.save()
    _recursive_map_model(d, 'rdf.models.Date')

    t = Concept.objects.get(resource__namespace=XS, resource__name='time')
    t.title = 'Time literal'
    t.description = 'The literal type used to store timestamps.'
    t.save()
    _recursive_map_model(t, 'rdf.models.Time')

    t = Concept.objects.get(resource__namespace=XS, resource__name='dateTime')
    t.title = 'Date-Time literal'
    t.description = 'Another literal type used to store timestamps.'
    t.save()
    _recursive_map_model(t, 'rdf.models.Time')

    d = Concept.objects.get(resource__namespace=XS, resource__name='duration')
    d.title='Duration Literal'
    d.description='The literal type used to store durations.'
    d.save()
    _recursive_map_model(d, 'rdf.models.Duration')

    d = Concept.objects.get(resource__namespace=XS, resource__name='decimal')
    d.title='Decimal Literal'
    d.description='The literal type used to store decimal numbers.'
    d.save()
    _recursive_map_model(d, 'rdf.models.Decimal')

    d = Concept.objects.get(resource__namespace=XS, resource__name='double')
    d.title='Double Literal'
    d.description='The literal type used to store double size floating point numbers.'
    d.save()
    _recursive_map_model(d, 'rdf.models.Float')

    d = Concept.objects.get(resource__namespace=XS, resource__name='float')
    d.title='Float Literal'
    d.description='The literal type used to store floating point numbers.'
    d.save()
    _recursive_map_model(d, 'rdf.models.Float')

    s = Concept.objects.get(resource__namespace=XS, resource__name='string')
    s.title = 'String Literal'
    s.description='The literal type used to store text values.'
    s.save()
    _recursive_map_model(s, 'rdf.models.String')

    p = Predicate.objects.get(resource__namespace=DC, resource__name='title')
    p.range = XS['string']
    p.save()

    p = Predicate.objects.get(resource__namespace=DC, resource__name='description')
    p.range = XS['string']
    p.save()


def _mark_internal_ontologies():
    from rdf.models import Ontology
    for o in Ontology.objects.all(): # IGNORE:E1101
        o.internal = True
        o.save()


def _recursive_map_model(t, model_name):
    """
    Can't remember what this does. Hnng :)
    """
    remaining, done = set((t,)), set()
    while 0 < len(remaining):
        base = remaining.pop()
        base.model_name = model_name
        base.save()
        done.add(base)
        for derived in base.derived.all():
            if derived not in done:
                remaining.add(derived)
    

def compiler_support():
    for l in Concept.objects.filter(literal=True):
        _compiler_support(l)
        
def _compiler_support(literal):
    """
    Creates an implicit literal and predicate pair imitating the ontology elements 
    that would appear in an ontology fragment constructed by mirroring the database 
    table underlying the parameter literal.  
    
    The query compiler uses the literal and predicate during the processing of 
    clauses that contain predicates using the parameter literal as the range. 
    """
    RDF, RDFS, DRDFS = \
        get((Namespace, 'rdf'), (Namespace, 'rdfs'), (Namespace, 'drdfs'))
    one_to_one = Cardinality.objects.get(domain='1', range='1')
    title = literal.title + ' (*)'
    description = 'Compiler support for %ss' % literal.title
    unique = (literal.namespace.code, literal.name)
    tr, _ = Resource.objects.get_or_create(
        namespace=DRDFS, name='_%s%s' % unique, type=RDFS['Literal'])
    t, _ = Concept.objects.get_or_create(
        resource=tr, 
        title=title,
        description=description,
        model_name=literal.model_name, 
        literal=True)
    pr, _ = Resource.objects.get_or_create(
        namespace=DRDFS, name='_%s%svalue' % unique, type=RDF['Property'])
    Predicate.objects.get_or_create(
        resource=pr, 
        domain=literal, 
        range=t,
        field_name='%s.value' % literal.model_name,
        cardinality=one_to_one, 
        title=title,
        description=description)


def predicate_spans():
    """
    Generates spanning predicates for all concepts.
    """
    
    def concept(c):
        for p in Predicate.objects.filter(domain=c):
            if invalid_segment(p):
                continue
            if p.literal:
                continue
            for q in egress(p):
                if invalid_segment(q):
                    continue
                if q.literal:
                    span(p, q)
                    continue
                for r in egress(q):
                    if invalid_segment(r):
                        continue
                    if r.literal:
                        span(p, q, r)
        
    def invalid_segment(p):
        return p.span \
            or p.Range in (Resource, Concept, Predicate) \
            or (p.literal and type(p.field) is AutoField)
        
    def egress(p):
        for _ in Predicate.objects.filter(domain=p.range):
            yield _
            
    def span(*predicates):
        """
        Creates a spanning predicate across the parameter predicates. The span 
        is not assigned to an ontology.
        """
        domain, range_ = predicates[0].domain, predicates[-1].range
        resource, _ = Resource.objects.get_or_create(
            namespace=_span_namespace(domain), 
            name=_span_name(*predicates), 
            type=Predicate.objects.type)
        span, _ = Predicate.objects.get_or_create(
            resource=resource, 
            domain=domain, 
            range=range_, 
            cardinality=_span_cardinality(*predicates),
            title=predicates[len(predicates)-1].title, 
            description=predicates[len(predicates)-1].description)
        for p, i in zip(predicates, range(0, len(predicates))):
            _SpanSegment.objects.get_or_create(span=span, predicate=p, ordinal=i)
        return span 
        
    for c in Concept.objects.filter(literal=False):
        concept(c)

def _span_namespace(concept):
    code = concept.namespace.code+'-spans'
    try:
        namespace = Namespace.objects.get(code=code)
    except Namespace.DoesNotExist:
        uri = concept.namespace.uri
        if '#' == uri[-1]:
            uri = uri[:-1] + '-spans' + '#'
        elif '/' == uri[-1]: 
            uri = uri[:-1] + '-spans' + '/'
        resource = Resource.objects.create(name=uri)
        description = 'Synthesized spanning predicates for %s' % code
        namespace = Namespace.objects.create(
            code=code, resource=resource, 
            title=concept.namespace.title + ' (spans)',
            description=description)
    return namespace

def _span_name(*predicates):
    segments = []
    for p in predicates:
        segments.append(u'_'.join((p.namespace.code, p.name))) 
    return u'__'.join(segments)

def _span_cardinality(*predicates):
    begin, end = predicates[0], predicates[-1]
    domain, range = begin.cardinality.domain, end.cardinality.range
    for p in predicates:
        if '*' != range and _greater_cardinality(range, p.cardinality.range):
            range = p.cardinality.range 
        if '*' != domain and _greater_cardinality(domain, p.cardinality.domain):
            domain = p.cardinality.domain
    return Cardinality.objects.get(domain=domain, range=range)
            
def _greater_cardinality(a, b):
    if '1' == a:
        return b in ('?', '+', '*')
    elif '?' == a:
        return b in ('+', '*')
    elif '+' == a:
        return '*' == b
    else:
        return False
    
    
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
