from django.core.exceptions import ObjectDoesNotExist

from rdf.models import Cardinality, Namespace, Ontology, Predicate, Resource, \
    Statement, Concept
from rdf.shortcuts import get

from rdf.serializers import _JC, _split_URI, _DXML 


RDF = get(Namespace, 'rdf')
RDFS = get(Namespace, 'rdfs')
OWL = get(Namespace, 'owl')
DC = get(Namespace, 'dc')
DRDFS = get(Namespace, 'drdfs')

RESOURCE, CONCEPT, LITERAL, PREDICATE = get(
    (Concept, RDFS, 'Resource'), 
    (Concept, RDFS, 'Class'), 
    (Concept, RDFS, 'Literal'), 
    (Concept, RDF, 'Property'))

RDF_RDF = _JC(RDF.uri, 'RDF')
RDF_DESCRIPTION = _JC(RDF.uri, 'Description')
RDF_RESOURCE = _JC(RDF.uri, 'resource')
RDF_ID = _JC(RDF.uri, 'ID')
RDF_ABOUT = _JC(RDF.uri, 'about')
RDF_PROPERTY = _JC(RDF.uri, 'Property')

RDFS_CLASS = _JC(RDFS.uri, 'Class')
RDFS_LITERAL = _JC(RDFS.uri, 'Literal')
RDFS_DATATYPE = _JC(RDFS.uri, 'Datatype')
RDFS_DOMAIN = _JC(RDFS.uri, 'domain')
RDFS_RANGE = _JC(RDFS.uri, 'range')
RDFS_LABEL = _JC(RDFS.uri, 'label')
RDFS_COMMENT = _JC(RDFS.uri, 'comment')
RDFS_ISDEFINEDBY = _JC(RDFS.uri, 'isDefinedBy')
RDFS_SUBCLASSOF = _JC(RDFS.uri, 'subClassOf')
RDFS_SUBPROPERTYOF = _JC(RDFS.uri, 'subPropertyOf')

OWL_ONTOLOGY = _JC(OWL.uri, 'Ontology')
OWL_CLASS = _JC(OWL.uri, 'Class')

DC_TITLE = _JC(DC.uri, 'title')
DC_DESCRIPTION = _JC(DC.uri, 'description')

DRDFS_MODEL = _JC(DRDFS.uri, 'model')
DRDFS_FIELD = _JC(DRDFS.uri, 'field')
DRDFS_CARDINALITY = _JC(DRDFS.uri, 'cardinality')
DRDFS_INTERNAL = _JC(DRDFS.uri, 'internal')


class _Deserializer(_DXML):
    
    def __init__(self, ontology_path, **options):
        _DXML.__init__(self,
            ontology_path, # IGNORE:E1101
            {RDF_RDF: self._trivial, # IGNORE:E1101
             RDF_DESCRIPTION: self._trivial, # IGNORE:E1101 
             OWL_ONTOLOGY: self._owl_ontology, 
             RDFS_CLASS: self._rdfs_class, 
             RDFS_LITERAL: self._rdfs_class, 
             RDFS_DATATYPE: self._trivial, 
             RDF_PROPERTY: self._rdf_property,},
             self._rdf_resource,
            **options)
        self._ontology = None
        self._superconcepts = []
        self._superpredicates = []
    
    def _postiter_hook(self):
        self._populate_superconcepts()
        
    def _populate_superconcepts(self):
        for t, bns, bname in self._superconcepts:
            b = None
            try: 
                b = Concept.objects.get(resource__namespace=bns, resource__name=bname)
            except Concept.DoesNotExist: # IGNORE:E1101 
                try: 
                    # Cheat!
                    r = Resource.objects.create(namespace=bns, name=bname)
                    b = Concept.objects.create(resource=r, name=bname)
                except Exception, x: # IGNORE:W0703 
                    self._except(Exception, x, '%s %s' % bns, bname) # IGNORE:E1101
            t.bases.add(b)
            t.save()

    def _populate_superpredicates(self):
        for t, bns, bname in self._superpredicates:
            b = None
            try: 
                b = Predicate.objects.get(resource__namespace=bns, resource__name=bname)
            except Predicate.DoesNotExist: # IGNORE:E1101 
                try: 
                    # Cheat!
                    r = Resource.objects.create(namespace=bns, name=bname)
                    b = Predicate.objects.create(resource=r, name=bname)
                except Exception, x: # IGNORE:W0703 
                    self._except(Exception, x, '%s %s' % bns, bname) # IGNORE:E1101
            t.bases.add(b)
            t.save()

    def _owl_ontology(self, e):
        ns_uri = e.get(RDF_ABOUT)
        namespace = Namespace.objects.get(resource__name=ns_uri)
        title = e.find(DC_TITLE)
        if not title is None:
            title = title.text
        if title is None:
            title = e.get(DC_TITLE)
        if title is None:
            title = namespace.uri
        description = e.find(DC_DESCRIPTION)
        description = title if description is None else description.text
        internal = e.find(DRDFS_INTERNAL)
        internal = True if internal == 'true' else False 
        match = Ontology.objects.filter(resource=namespace.resource) 
        ontology = None
        if 1 > match.count():
            ontology = Ontology(
                resource=namespace.resource,
                title=title,
                description=description,
                internal=internal)
            yield ontology
        else:
            ontology = match[0]
            ontology.resource = namespace.resource
            ontology.internal = internal
            ontology.save()
        self._ontology = ontology
                    
    def _rdfs_class(self, e):
        try:
            label = e.find(RDFS_LABEL).text
            literal = True if (RDFS_LITERAL == e.tag) else False 
            resource = self._rdfs_class_resource(e, label, literal)
            yield resource 
            concept = self._rdfs_class_concept(e, label, literal, resource)
            yield concept
        except Exception, x: # IGNORE:W0703
            self._except(Exception, x, # IGNORE:E1101
'Failed to parse concept, use --verbosity, --traceback and --graceful to diagnose.')

    def _rdfs_class_isdefinedby(self, e, label):
        isdefinedby = e.find(RDFS_ISDEFINEDBY)
        if not isdefinedby is None:
            ns_uri = isdefinedby.get(RDF_RESOURCE)
        elif not self._ontology is None:
            ns_uri = self._ontology.namespace.uri # IGNORE:E1103
        else:
            raise Exception('unable to resolve `%s` to ontology' % label)
        return isdefinedby, ns_uri
    
    def _rdfs_class_resource(self, e, label, literal):
        isdefinedby, ns_uri = self._rdfs_class_isdefinedby(e, label)
        namespace=Namespace.objects.get(resource__name=ns_uri)
        about = e.get(RDF_ABOUT)
        if isdefinedby and about:
            assert ns_uri == about[:len(ns_uri)]
        name = about[len(ns_uri):] if about else label
        match = Resource.objects.filter(namespace=namespace, name=name)
        if 1 > match.count():
            resource = Resource(
                namespace=namespace, 
                name=name,
                type=LITERAL if literal else CONCEPT)
        else:
            resource = match[0]
            resource.type = LITERAL if literal else CONCEPT
        return resource
    
    def _rdfs_class_concept(self, e, label, literal, resource): 
        description = e.find(RDFS_COMMENT)
        description = label.title() if description is None else description.text
        model_name = e.find(DRDFS_MODEL)
        if model_name is not None:
            model_name = model_name.text
        match = Concept.objects.filter(resource=resource)
        concept = None
        if 1 > match.count():
            concept = Concept( 
                resource=resource,
                title=label.title(), 
                description=description,
                literal=literal)
            if model_name is not None:
                concept.model_name = model_name
        else:
            concept = match[0]
            concept.title = label.title()
            concept.description = description
            if model_name is not None:
                concept.model_name = model_name
            concept.literal = literal
        self._rdfs_class_subclassof(e, concept)
        return concept

    def _rdfs_class_subclassof(self, e, concept):
        b = e.find(RDFS_SUBCLASSOF)
        if b is None: return
        b = b.get(RDF_RESOURCE)
        if b is None: return
        bns, bname = _split_URI(b)
        self._superconcepts.append((concept, bns, bname))                

    def _rdf_property(self, e):
        try: 
            label = e.find(RDFS_LABEL).text
            resource, create = self._rdf_property_resource(e, label)
            if create is True: yield resource
            domain, create = _rdf_property_domain(e)
            if create is True: yield domain
            range, create = _rdf_property_range(e) 
            if create is True: yield range
            field_name = _rdf_property_field_name(e)
            cardinality = _rdf_property_cardinality(e)
            description = _rdf_property_dc_description(e, label)
            match = Predicate.objects.filter(resource=resource)
            if 1 > match.count():
                predicate = Predicate(
                    resource=resource, 
                    title=label.title(), 
                    description=description, 
                    domain=domain, 
                    range=range, 
                    cardinality=cardinality, 
                    field_name=field_name)
            else:
                predicate = match[0]
                predicate.title = label.title()
                predicate.description = description
                predicate.domain = domain
                predicate.range = range
                predicate.cardinality = cardinality
                predicate.field_name = field_name
            self._rdf_property_subpropertyof(e, predicate)
            yield predicate
        except Exception, x: # IGNORE:W0703
            self._except(Exception, x, 'failed to parse property `%s`' % resource) # IGNORE:E1101
    
    def _rdf_property_resource(self, e, label):
        create = False
        ns_uri = e.find(RDFS_ISDEFINEDBY)
        if not ns_uri is None:
            ns_uri = ns_uri.get(RDF_RESOURCE)
        elif not self._ontology is None:
            ns_uri = self._ontology.namespace.uri # IGNORE:E1103
        namespace = Namespace.objects.get(resource__name=ns_uri)
        about = e.get(RDF_ABOUT)
        name = about[len(ns_uri):] if about else label
        match = Resource.objects.filter(namespace=namespace, name=name)
        if 1 > match.count():
            resource = Resource(namespace=namespace, name=name, type=PREDICATE)
            create = True
        else:
            resource = match[0]
        return resource, create
    
    def _rdf_property_subpropertyof(self, e, predicate):
        b = e.find(RDFS_SUBPROPERTYOF)
        if b is None: return
        b = b.get(RDF_RESOURCE)
        if b is None: return
        bns, bname = _split_URI(b)
        self._superpredicates.append((predicate, bns, bname))    
    
    def _rdf_resource(self, e):
        TNS, tn = _split_URI(e.tag)
        concept = None
        try:
            concept = TNS[tn]
        except ObjectDoesNotExist, x:
            self._except(ObjectDoesNotExist, x, 'unable to resolve tag `%s`' % e.tag) # IGNORE:E1101
        if concept is None or not isinstance(concept, Concept):
            return
        
        uri = e.get(RDF_ABOUT)
        if uri is None:
            uri = e.get(RDF_ID) # Either about or ID are required
        RNS, rn = _split_URI(uri)
        if RNS is None:
            RNS = self._ontology.namespace # Best guess
        match = Resource.objects.filter(namespace=RNS, name=rn)
        resource = None
        if 1 > match.count(): 
            resource = Resource(namespace=RNS, name=rn, type=concept)
            yield resource
        else:
            resource = match[0]
            
        custom_model = _rdf_resource_map_custom_model(e, resource, concept)
        if not custom_model is None: yield custom_model
        dc_title = _rdf_resource_dc_title(e, resource)
        if not dc_title is None: yield dc_title
        dc_description = _rdf_resource_dc_description(e, resource)
        if not dc_description is None: yield dc_description
                
def _rdf_property_domain(e):
    create = False
    de = e.find(RDFS_DOMAIN)
    if de is None:
        domain = RESOURCE
    else:
        dns, dn = _split_URI(de.get(RDF_RESOURCE))
        try: 
            domain = Concept.objects.get(resource__namespace=dns, resource__name=dn)
        except Concept.DoesNotExist: # IGNORE:E1101
            r, _ = Resource.objects.get_or_create(
                namespace=dns, name=dn, defaults=dict(type=CONCEPT))
            domain = Concept(resource=r, title=dn.title())
            create = True
    return domain, create

def _rdf_property_range(e):
    create = False
    re = e.find(RDFS_RANGE)
    if re is None:
        range = RESOURCE
    else:
        rns, rn = _split_URI(re.get(RDF_RESOURCE))
        assert not rns is None
        assert '' != rn
        try:
            r, _ = Resource.objects.get_or_create(
                namespace=rns, name=rn, defaults=dict(type=CONCEPT))
            range = Concept.objects.get(resource=r)
        except Concept.DoesNotExist: # IGNORE:E1101
            range = Concept(resource=r, title=rn.title())
            create = True
    return range, create
                
def _rdf_property_field_name(e):
    field_name = e.find(DRDFS_FIELD)
    if field_name is not None:
        field_name = field_name.text
    return field_name
                
def _rdf_property_cardinality(e):
    cardinality = e.find(DRDFS_CARDINALITY)
    if cardinality is None:
        cardinality = Cardinality.objects.get(domain='*', range='*')
    else:
        dcard, rcard = cardinality.text.split(':')
        dcard, rcard = dcard.strip(), rcard.strip()
        cardinality = Cardinality.objects.get(domain=dcard, range=rcard)
    return cardinality

def _rdf_property_dc_description(e, label):
    description = e.find(RDFS_COMMENT)
    description = label if description is None else description.text
    return description
                
def _rdf_resource_map_custom_model(e, resource, concept):
    if concept.Model is Resource:
        return None
    kwargs = dict(resource=resource)
    for p in concept.mandatory_predicates:
        c = e.find(_JC(p.resource.namespace.uri, p.name))
        if c is None: continue
    match = concept.Model.objects.filter(**kwargs)
    return None if 0 < match.count() else concept.Model(**kwargs)
            
# The following two functions can (and should) be extended into a single generic 
# function that handles any predicate (instead of just dc:title and dc:description)
            
def _rdf_resource_dc_title(e, resource):
    title = e.find(DC_TITLE)
    if title is None: return None
    kw = dict(subject=resource, predicate=DC['title'])
    match = Statement.objects.filter(**kw)
    if 0 < match.count():
        assert match.object == title.text
        return None
    kw['object'] = title.text
    return Statement(**kw)

def _rdf_resource_dc_description(e, resource):
    description = e.find(DC_DESCRIPTION)
    if description is None: return None 
    kw = dict(subject=resource, predicate=DC['description'])
    match = Statement.objects.filter(**kw)
    if 0 < match.count():
        assert match.object == description.text
        return None
    kw['object'] = description.text
    return Statement(**kw)

