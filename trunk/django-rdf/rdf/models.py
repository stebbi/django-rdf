"""
Django models implementing an RDF engine.

A 'name' belongs to a namespace. A 'code' does not. Examples:

The name of a namespace is the full URI of the namespace. The code of the namespace,
on the other hand, is just the shorthand used to indicate the namespace in the current
context.

For example, the name of the RDF namespace starts with 'http://www.w3' and the code
is usually 'rdf'.

And, an example of a URI could be as follows:

    URI:        http://example.com/namespace/xyz 
    namespace:  http://example.com/namespace/
    name:       xyz
    code:       example:xyz (assuming the code 'example' for the namespace)

Names are globally unique or unique within a namespace. Codes are less restricted.
"""

from contextlib import contextmanager
from datetime import date, datetime

from django.db.models import Manager, Model, BooleanField, CharField, DateField, \
    DateTimeField, DecimalField, EmailField, FloatField, IntegerField, TextField, \
    ManyToManyField, Q, get_model, get_models
from django.db.models.fields.related import ForeignKey
from django.dispatch import dispatcher

from rdf.managers import \
    NamespaceManager, OntologyManager, PredicateManager, ResourceManager, \
    StatementManager, ConceptManager
from rdf.shortcuts import import_class
from django.db.models.query import EmptyQuerySet


class Resource(Model): 

    namespace = ForeignKey(
        'Namespace', null=True, blank=True, related_name='prefix', db_index=True)
    name = CharField( max_length=255, db_index=True)
    type = ForeignKey(
        'Concept', related_name='generic_resources', null=True, blank=True, db_index=True)

    issued = DateTimeField(default=datetime.now)

    objects = ResourceManager()

    class Admin: # IGNORE:W0232
        list_display = ('name', 'namespace', 'uri', 'type', 'issued')
        list_filter = ('namespace', 'type', 'issued')
        search_fields = ('name',)
        ordering = ('name',)

    class Meta: # IGNORE:W0232
        unique_together = ('namespace', 'name')

    def __unicode__(self):
        return self.code

    def __eq__(self, other):
        return type(self) == type(other) \
            and self.namespace == other.namespace \
            and self.name == other.name

    def __hash__(self):
        return hash(unicode(self).lower())

    def _geturi(self):
        return u''.join((self.namespace.uri, self.name)) if self.namespace else self.name # IGNORE:E1101
    uri = property(_geturi)

    def get_absolute_url(self):
        return self.uri

    def __getcode(self):
        return u':'.join((self.namespace.code, self.name)) if self.namespace else self.name # IGNORE:E1101
    code = property(__getcode)

    def __getmangled(self):
        prefix = self.namespace.mangled # IGNORE:E1101
        suffix = self.name
        return u'%s__%s' % (prefix, suffix)
    mangled = property(__getmangled)
    

class Literal(object): # IGNORE:R0903
    '''
    Django doesn't support model inheritance. This class is used to indicate that
    a model is a type of RDF literal:

        class String(Model, Literal):
            ...
            
    An RDF literal is materialized as a restricted form of the concept type. If Django
    supported model inheritance then this model would specialize from the Concept model
    but for the moment the workaround employs a Boolean `literal` field to indicate 
    when a concept is actually a literal.
    '''
    pass


class Namespace(Model):

    code = CharField(max_length=31, unique=True, db_index=True)
    resource = ForeignKey(Resource, unique=True, related_name='ns', db_index=True)

    title = CharField(max_length=127, db_index=True)
    description = TextField()

    issued = DateTimeField(default=datetime.now)

    objects = NamespaceManager()

    post_save = object()

    _dict_enabled = True

    class Admin: 
        list_display = ('code', 'uri')
        ordering = ('code',)
        search_fields = ('code', 'resource__name',)

    def disable_dict_lookups(cls):
        cls._dict_enabled = False
    disable_dict_lookups = classmethod(disable_dict_lookups)

    def enable_dict_lookups(cls):
        cls._dict_enabled = True
    enable_dict_lookups = classmethod(enable_dict_lookups)

    @contextmanager
    def disabled_dict_lookups(cls):
        cls.disable_dict_lookups()
        yield
        cls.enable_dict_lookups()
    disabled_dict_lookups = classmethod(disabled_dict_lookups)

    def __unicode__(self):
        return self.code

    def __eq__(self, other):
        return self.code.lower() == other.code.lower() # IGNORE:E1101

    def __hash__(self):
        return hash(self.code.lower()) # IGNORE:E1101

    def save(self):
        super(self.__class__, self).save()
        dispatcher.send(signal=self.post_save, sender=self.__class__, instance=self)

    def __getname(self):
        return self.resource.name # IGNORE:E1101
    name = property(__getname)

    def __geturi(self):
        return self.resource.uri # IGNORE:E1101
    uri = property(__geturi)

    def get_absolute_url(self):
        return self.uri

    def __getmangled(self):
        return self.code.upper().replace('-', '_') # IGNORE:E1101
    mangled = property(__getmangled)

    def __gettype(self): # IGNORE:R0201
        return Concept.objects.type
    type = property(__gettype)

    def __getitem__(self, name):
        """
        This is a highly convenient shorthand that supports expressions like 
        
            RDF['Property', 'about', 'subject', 'predicate', 'object']
            
        and returns instances of the appropriate models - in the example above, 
        a concept and for predicates. 
        
        It somewhat unfortunately can't be used in any code that might be invoked 
        from the templating system. 
        """
        if not self._dict_enabled:
            return super(Namespace, self).__getitem__(name)
        if type(name) in (tuple, list):
            return [self[i] for i in name]
        r = Resource.objects.get(namespace=self, name=name)
        if not r.type is Resource:
            Model = import_class(r.type.model_name) # IGNORE:W0621
            if not Model is Resource:
                r = Model.objects.get(resource=r)
        return r

from rdf.permissions import update_namespace_permissions
dispatcher.connect(update_namespace_permissions, sender=Namespace, signal=Namespace.post_save)


class Ontology(Model):
    """
    Represents an OWL ontology, such as the OWL ontology itself and derived ontologies 
    including the Dublin Core ontologies etc.
    """

    # An ontology has an associated resource.
    resource = ForeignKey(Resource, unique=True)
   
    internal = BooleanField(default=False)
    
    title = CharField(max_length=127, db_index=True)
    description = TextField()

    # Creation timestamp.
    issued = DateTimeField(default=datetime.now, db_index=True)
    
    objects = OntologyManager()
    
    class Admin:
        list_display = ('title', 'namespace', 'description')
        ordering = ('title',)
        search_fields = ('title', 'description')
       
    class Meta:
        verbose_name = 'Ontology'
        verbose_name_plural = 'Ontologies'

    def __unicode__(self):
        return self.namespace.code
    
    def __getnamespace(self):
        return Namespace.objects.get(resource=self.resource)
    namespace = property(__getnamespace)
    
    def __getname(self):
        return self.resource.name
    name = property(__getname)
    
    def __getcode(self):
        return self.namespace.code
    code = property(__getcode)
    
    def __geturi(self):
        return self.resource.name # IGNORE:E1101
    uri = property(__geturi)
    
    def __getconcepts(self):
        return Concept.objects.filter(resource__namespace=self.namespace)
    concepts = property(__getconcepts)
        

class Concept(Model):
    """
    Materializes resources of the RDFS Class type.
    """

    # Each concept object is a resource in its own right. 
    # This is implemented using aggregation, not model inheritance
    resource = ForeignKey(Resource, unique=True, related_name='resource_type', db_index=True)

    # Support for multiple inheritance for concepts.
    # A concept object inherits its bases
    bases = ManyToManyField('self', symmetrical=False, related_name='derived')

    title = CharField(max_length=127, db_index=True)
    description = TextField()

    # Absolute name of a model
    model_name = CharField(max_length=63, db_index=True) 

    # True iff the object is a literal (string, number...), else False
    literal = BooleanField(default=False)

    # Creation timestamp
    issued = DateTimeField(default=datetime.now, db_index=True)

    objects = ConceptManager()
    
    post_save = object()

    class Admin:
        list_display = ('title', 'namespace', 'name', 'uri', 'model_name',)
        list_filter = ('model_name',)
        ordering = ('title',)
        search_fields = ('title',)

    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('model_name'):
            kwargs['model_name'] = Concept.objects.DEFAULT_MODEL_NAME
        super(self.__class__, self).__init__(*args, **kwargs) # IGNORE:W0142

    def __eq__(self, other):
        return type(self) == type(other) and self.resource == other.resource
    
    def __hash__(self):
        return hash(self.resource)

    def __unicode__(self):
        return unicode(self.resource)

    def save(self):
        # Check that the model name refers to a real model:
        model_exists = False
        for m in get_models():
            if u'.'.join((m.__module__, m.__name__)) == self.model_name:
                model_exists = True
                break
        assert model_exists, \
            'type must be associated with a real model, not %s' % self.model_name
        # Save, signal and... done:
        super(self.__class__, self).save()
        dispatcher.send(signal=self.post_save, sender=self.__class__, instance=self)

    def __getnamespace(self):
        """
        Returns the namespace this concept belongs to. 
        """
        return self.resource.namespace # IGNORE:E1101
    namespace = property(__getnamespace)

    def __getname(self):
        """
        Returns the local name of the concept, without the containing namespace.
        """
        return self.resource.name
    name = property(__getname)

    def __getontology(self):
        """
        Returns the ontology this concept belongs to. 
        """
        try:
            return Ontology.objects.get(resource=self.namespace.resource) # IGNORE:E1101
        except Ontology.DoesNotExist: # IGNORE:E1101
            return None
    ontology = property(__getontology)

    def __getinternal(self):
        return self.ontology.internal
    internal = property(__getinternal)

    def __gettype(self): # IGNORE:R0201
        return self.resource.type # IGNORE:E1101
    type = property(__gettype)

    def __getmodel(self):
        """
        Returns the Django model that materializes this concept. This is either 
        the RDF Resource model (in case of a generic concept) or some other model 
        that stores only instances of this exact concept.
        """
        return import_class(self.model_name)
    Model = property(__getmodel)
    
    def __isgeneric(self):
        return self.Model is Resource or self.literal
    generic = property(__isgeneric)
    
    def __getpkcolumn(self):
        """
        Returns the name of the database column containing the primary key for 
        this concept.
        """
        return self.Model._meta.pk.attname # IGNORE:W0212
    pk_column = property(__getpkcolumn)

    def __getcode(self):
        """
        Returns the qualified name of the concept instance, consisting of the 
        namespace code and the local name.
        """
        return u':'.join((self.namespace.code, self.name))
    code = property(__getcode)
    
    def __getmangled(self):
        return self.resource.mangled # IGNORE:E1101
    mangled = property(__getmangled)

    def __geturi(self):
        """
        Returns the URI for the concept instance.
        """
        return self.resource.uri # IGNORE:E1101
    uri = property(__geturi)

    def get_absolute_url(self):
        """
        Returns the URI for the concept instance.
        """
        return self.uri

    def get_predicates(self, *predicate_codes, **kwargs):
        """
        Shorthand for retrieving predicates applicable to the concept instance.
        """
        # Prepare the predicate query:
        mandatory = kwargs['mandatory'] if kwargs.has_key('mandatory') else None
        literal = kwargs['literal'] if kwargs.has_key('literal') else None
        cardinalities = \
            Cardinality.mandatory_range_Q if mandatory is True else \
            Cardinality.optional_range_Q if mandatory is False else \
            Q() # Allow any cardinality
        filters = dict(domain=self)
        if not literal is None:
            filters['range__literal'] = literal
        # Fetch the matching predicates:
        qs = Predicate.objects.filter(cardinalities, **filters) # IGNORE:W0142
        # Now fetch predicates for any base concepts and join the resulting query sets:
        for b in self.bases.all(): # IGNORE:E1101
            filters['domain'] = b
            qs |= Predicate.objects.filter(cardinalities, **filters) # IGNORE:W0142
        # Finally filter the results using the parameter predicate codes:
        n = len(predicate_codes)
        if 0 < n:
            prefix, suffix = predicate_codes[0].split(':')
            q = Q(resource__namespace__code=prefix, name=suffix)
            for code in predicate_codes[1:]:
                prefix, suffix = code.split(':')
                q |= Q(resource__namespace__code=prefix, name=suffix)
            qs = qs.filter(q)
        return qs
    
    def __get_all_predicates(self):
        """
        Returns all predicates with the concept instance as the domain.
        """
        if not hasattr(self, '_predicates'):
            setattr(self, '_predicates', self.get_predicates())
        return getattr(self, '_predicates')
    predicates = property(__get_all_predicates)

    def __get_mandatory_predicates(self):
        """
        Returns all predicates with the concept instance as the domain, that 
        must be applied to every resource of that concept.
        """
        if not hasattr(self, '_mandatory_predicates'):
            setattr(self, '_mandatory_predicates', self.get_predicates(mandatory=True))
        return getattr(self, '_mandatory_predicates')
    mandatory_predicates = property(__get_mandatory_predicates)
    
    def __get_mandatory_literals(self):
        """
        Returns all predicates with the concept instance as the domain, that 
        may be omitted from resources of that concept.
        """
        if not hasattr(self, '_mandatory_literals'):
            setattr(self, '_mandatory_literals', 
                    self.get_predicates(mandatory=True, literal=True))
        return getattr(self, '_mandatory_literals')
    mandatory_literals = property(__get_mandatory_literals)

    def __get_optional_predicates(self):
        if not hasattr(self, '_optional_predicates'):
            setattr(self, '_optional_predicates', self.get_predicates(mandatory=False))
        return getattr(self, '_optional_predicates')
    optional_predicates = property(__get_optional_predicates)
    
    def __get_reverse_predicates(self):
        if not hasattr(self, '_reverse_predicates'):
            setattr(self, '_reverse_predicates', 
                Predicate.objects.filter(range=self))
        return getattr(self, '_reverse_predicates')
    reverse_predicates = property(__get_reverse_predicates)

    def __get_concepts(self):
        if not hasattr(self, '_concepts'):
            setattr(self, '_concepts', 
                    self.get_predicates(literal=False))
        return getattr(self, '_concepts')
    concepts = property(__get_concepts)

    def __get_literals(self):
        if not hasattr(self, '_literals'):
            setattr(self, '_literals', 
                    self.get_predicates(literal=True))
        return getattr(self, '_literals')
    literals = property(__get_literals)

    def __get_resources(self):
        if self.Model is Resource:
            setattr(self, '_resources', self.generic_resources) # IGNORE:E1101
        else:
            setattr(self, '_resources', self.Model.objects.all())
        return getattr(self, '_resources')
    resources = property(__get_resources)

from rdf.permissions import update_type_permissions
dispatcher.connect(update_type_permissions, sender=Concept, signal=Concept.post_save)


CARDINALITIES = (
    ('1',  'Predicate is applied to every resource'),
    ('?',  'Predicate is applied zero or one times to each resource'),
    ('+',  'Predicate is applied one or more times to each resource'),
    ('*',  'Predicate is applied zero or more times to each resource'),
    ('1S', 'Predicate is applied to every resource and forms time series'),
    ('?S', 'Predicate is applied zero or one times and forms time series'),
    ('+S', 'Predicate is applied one or more times and forms time series'),
    ('*S', 'Predicate is applied zero or more times and forms time series'),)

def _cardinality_Q(**cardinalities): 
    qq = []
    for r in cardinalities['range']:
        if cardinalities.has_key('domain'):
            for d in cardinalities['domain']:
                qq.append(Q(cardinality__domain=d, cardinality__range=r))
        else:
            qq.append(Q(cardinality__range__exact=r))
    cardinalities = qq[0]
    for _ in qq:
        cardinalities |= _
    return cardinalities

class Cardinality(Model):
    """
    Utility model used to keep track of predicate cardinalities. 
    """

    domain = CharField(max_length=2, choices=CARDINALITIES, default='*')
    range = CharField(max_length=2, choices=CARDINALITIES, default='*')
    # Range is an awkward field name, because __range is also a filter modifier
    # for query sets, like __exact and __contains.
    
    objects = Manager()

    class Meta:
        unique_together = ('domain', 'range')

    def __unicode__(self):
        return u'-'.join((self.domain, self.range))

    mandatory_codes = ('1', '+', '1S', '+S')
    optional_codes = ('?', '*', '?S', '*S')
    
    mandatory_range_Q = _cardinality_Q(range=mandatory_codes)
    optional_range_Q = _cardinality_Q(range=optional_codes)


class Predicate(Model):
    """
    Materializes RDF Property instances.
    """

    resource = ForeignKey(Resource, unique=True, db_index=True)

    domain = ForeignKey(Concept, related_name='domain', db_index=True)
    range = ForeignKey(Concept, related_name='range', null=True, blank=True, db_index=True)
    cardinality = ForeignKey(Cardinality)
    
    bases = ManyToManyField('self', symmetrical=False, related_name='derived')
    
    # Absolute name, e.g. <Model name>.<field name>
    field_name = CharField(max_length=63, null=True, blank=True, db_index=True) 

    title = CharField(max_length=63, db_index=True)
    description = TextField()

    issued = DateField(default=date.today, db_index=True)

    objects = PredicateManager()
    
    post_save = object()

    class Admin: # IGNORE:W0232
        list_display = ('title', 'namespace', 'name', 'domain', 'range', 'issued',)
        list_filter = ('domain', 'range', 'issued',)
        ordering = ('title',)
        search_fields = ('title', 'description')

    def __unicode__(self):
        return u':'.join((u'*', self.code, u'*')) 

    def __eq__(self, other):
        return self.name.lower() == other.name.lower() # IGNORE:E1101

    def __hash__(self):
        return hash(self.name.lower()) # IGNORE:E1101

    def save(self):
        super(self.__class__, self).save()
        dispatcher.send(signal=self.post_save, sender=self.__class__, instance=self)
    
    def __getnamespace(self):
        """
        Returns the namespace of this predicate.
        """
        return self.resource.namespace # IGNORE:E1101
    namespace = property(__getnamespace)

    def __getontology(self):
        """
        Returns the ontology the predicate belongs to.
        """
        try:
            return Ontology.objects.get(resource=self.namespace.resource) # IGNORE:E1101
        except Ontology.DoesNotExist: # IGNORE:E1101
            return None
    ontology = property(__getontology)

    def __getinternal(self):
        return self.ontology.internal if self.ontology else False
    internal = property(__getinternal)

    def __getname(self):
        return self.resource.name
    name = property(__getname)

    def __getcode(self):
        """
        Returns the code of the predicate, consisting of the namespace code and 
        the predicate name.
        """
        return u':'.join((self.namespace.code, self.resource.name))
    code = property(__getcode)

    def __getmangled(self):
        """
        Returns the mangled predicate code, suitable for using as a python 
        object attribute name with hasattr, getattr, setattr.
        """
        return self.resource.mangled # IGNORE:E1101
    mangled = property(__getmangled)

    def __geturi(self):
        """
        Returns the full URI for the predicate.
        """
        return self.resource.uri # IGNORE:E1101
    uri = property(__geturi)

    def get_absolute_url(self):
        """
        Returns the full URI for the predicate.
        """
        return self.uri

    def __gettype(self): # IGNORE:R0201
        return Predicate.objects.type
    type = property(__gettype)

    def __getdomainmodel(self):
        """
        Returns the class object that is the required type of the subjects of
        all statements using this predicate. Required to always return a class.
        """
        return self.domain.Model # IGNORE:E1101
    Domain = property(__getdomainmodel)

    def __getrangemodel(self):
        """
        Returns the class object that is the required type of the objects of
        all statements using this predicate, if applicable. Returns None if
        not applicable.
        """
        return self.range.Model if self.range else None # IGNORE:E1101
    Range = property(__getrangemodel)
    
    def __isliteral(self):
        """
        A literal predicate has a literal for a range.
        """
        return self.range.literal # IGNORE:E1101
    literal = property(__isliteral)
    
    def __isfilter(self):
        """
        A predicate with a literal for a domain is a literal filter predicate. 
        These predicates filter resource attributes, for example by computing the 
        length of a string literal.
        """
        return self.domain.literal # IGNORE:E1101
    filter = property(__isfilter)
    
    def __isgeneric(self):
        """
        A generic predicate stores statements using the RDF Statement model. 
        Other predicates store statements in specific columns in other tables.
        """
        return self.field_name is None
    generic = property(__isgeneric)
    
    def __isspan(self):
        """
        True if and only if the predicate instance is a span consisting of multiple 
        atomic predicates.
        """
        return 0 < _SpanSegment.objects.filter(span=self).count()
    span = property(__isspan)
    
    def __getsegments(self):
        """
        Returns a query set containing the predicate segments of this span, or an 
        empty query set if this instance is not a span.
        """
        if not hasattr(self, '_segments'):
            setattr(self, '_segments', 
                _SpanSegment.objects.filter(span=self).order_by('ordinal'))
        return getattr(self, '_segments')
    segments = property(__getsegments)
    
    def __getfield(self):
        """
        Returns the model field that stores the objects of statements using this 
        predicate. If the predicate is generic then either the object field of 
        the Statement model is returned, or (in case of a predicate with a literal 
        range) the value field of the applicable literal model (the string model, 
        for example).
        """ 
        if self.field_name is None:
            if self.literal is True:
                f = self.range.Model._meta.get_field('value') # IGNORE:E1101
            else:
                f = Statement._meta.get_field('object_resource') # IGNORE:E1101
        else:
            _ = self.field_name.split('.') # IGNORE:E1101
            app_label, model_name, field_name = _[-4].lower(), _[-2], _[-1]
            f = get_model(app_label, model_name)._meta.get_field(field_name) # IGNORE:W0212
        return f
    field = property(__getfield)
    
    def __getdbcolumn(self):
        """
        Returns the name of the underlying database column.
        """
        field = self.field
        db_column = field.db_column
        if db_column is None:
            db_column = field.attname
        return db_column
    db_column = property(__getdbcolumn)
    
    def __getfilters(self):
        """
        Returns a query set with the filter predicate applicable for the domain of 
        the predicate instance. If, for example, the predicate instance returns a 
        string, then the applicable filters are all the available string filters
        (such as string length, etc.)
        """
        return Predicate.objects.filter(domain=self.range) \
            if self.literal else EmptyQuerySet()
    filters = property(__getfilters)

    def locate_resource(self, arg, required=True):
        """
        Locates a resource for the parameter 'arg'.
            - If arg is a resource then arg is returned
            - If arg is a Model instance then arg.resource is returned

        If no resource can be found then an Exception is raised if the 'required'
        parameter is True or not provided, else None is returned if 'required'
        is non-true.

        The predicate is responsible for using the subject argument to determine
        the subject resource stored in the Statement instance.

        The predicate is responsible for using the object argument to determine
        the object resource stored in the Statement instance, or otherwise ensure
        that the object reference is properly stored. If no object argument is
        provided then the statement consists only of the subject and predicate.
        """
        if isinstance(arg, Resource):
            return arg
        if isinstance(arg, Model):
            if hasattr(arg, 'resource') or hasattr(arg, 'resource_id'):
                return arg.resource
        if required:
            raise Exception("unable to determine resource for '%s'" % arg)
        return None
    locate_resource = classmethod(locate_resource)


from rdf.permissions import update_predicate_permissions
dispatcher.connect(update_predicate_permissions, sender=Predicate, signal=Predicate.post_save)


class _SpanSegment(Model):
    """
    Internal model for tracking the composition of spanning predicates.
    """
    
    span = ForeignKey(Predicate, related_name='spans')
    predicate = ForeignKey(Predicate, related_name='segment_set')
    ordinal = IntegerField() # The order of the segment, in the span

    objects = Manager()
    
    def save(self):
        if self.predicate.span: # IGNORE:E1101
            raise Exception('Invalid span - contains another span (%s)' % self.predicate)
        else:
            super(_SpanSegment, self).save()
            
    def __unicode__(self):
        return u' '.join((self.span.code, self.predicate.code, unicode(self.ordinal))) # IGNORE:E1101


class Statement(Model):
    """
    Represents an RDF statement, consisting of subject, predicate and object.
        'subject': The subject of the statement
        'predicate': The statement predicate
        'object': The (optional) object of the statement

    Optional metadata includes:
        'issued': creation timestamp
        'reified': resource used to refer to the statement in other statements
        'category': resource used to group the statement with other statements
        'ordinal': resource used to establish a predicate-specific ordering

    Statements are immutable. Don't alter a statement, instead delete it and
    create a new one instead.
    """
    reified = ForeignKey(Resource, unique=True, null=True, blank=True, related_name='reified')

    subject = ForeignKey(Resource, related_name='subject', db_index=True)
    predicate = ForeignKey(Predicate, db_index=True)
    object_resource = ForeignKey(Resource, related_name='object', null=True, blank=True, db_index=True)

    issued = DateTimeField(default=datetime.now)

    objects = StatementManager()

    def __init__(self, *args, **kwargs):
        # from pdb import set_trace; set_trace()
        needs_object, object_values = False, None
        p = kwargs['predicate'] if kwargs.has_key('predicate') else None
        if p:
            s = kwargs['subject'] if kwargs.has_key('subject') else None
            assert s is not None
            if type(s) is not Resource:
                kwargs['subject'] = p.locate_resource(s)
            # Six possibilities for the object argument:
            #    1. No object.
            #    2. Object resource, as a resource.
            #    3. Object resource, as a model.
            #    4. Object literal, as a model.
            #    5. Object literal, as a value.
            #    6. Object literal, as a value dictionary.
            # Option 1, if no 'object' argument:
            o = kwargs['object'] if kwargs.has_key('object') else None
            if o:
                del kwargs['object']
                r = p.locate_resource(o, required=False)
                if r:
                    # Covers options 2, 3:
                    kwargs['object_resource'] = r
                else:
                    # Options 4-6 continued below...
                    needs_object, object_values = True, o
        super(self.__class__, self).__init__(*args, **kwargs) # IGNORE:W0142
        if needs_object:
            self.__object = self._locate_and_assign_object(object_values)

    def save(self):
        save_object_required = \
            self.pk is None and \
            hasattr(self, '_Statement__object') and self.__object is not None and \
            (not hasattr(self, 'object_resource') or self.object_resource is None)
        super(self.__class__, self).save()
        if save_object_required:
            o = self.__object
            o.statement = self
            o.save() # IGNORE:E1103

    def __getobject(self):
        if not hasattr(self, '_Statement__object'):
            self.__object = self._locate_object() # IGNORE:E1101
        return self.__object
    # There should NOT be a __setobject method; statements are immutable.
    object = property(__getobject)

    def __unicode__(self):
        s, p = unicode(self.subject), unicode(self.predicate)
        o = self.object_resource
        if not o:
            o = unicode(self.object) if self.object else '--'
        return u' : '.join((unicode(s), unicode(p), unicode(o)))

    def _locate_and_assign_object(self, object_values):
        """
        The arguments are a statement and the object values for the statement.
        The statement invokes its own predicate to assist with object management.
    
        There are three possibilities for the object values:
    
            1. A literal (model instance) - statement assigned, instance returned.
               The type of the literal must match the predicate range.
    
            2. A value other than a dictionary - same as passing a dictionary with
               that value assigned to the 'value' key.
    
            3. A dictionary of values - a model instance of the predicate's range
               is creaed and populated with the dictionary values.
    
        In the third case, the literal is not saved to the database. The statement
        save method is responsible for that.
        """
        # Option 1, literal model:
        Range = self.predicate.Range # IGNORE:E1101
        if type(object_values) is Range:
            return object_values
        # Option 2, value other than dictionary:
        if not isinstance(object_values, dict):
            object_values = {'value': object_values}
        # Option 3, create a literal model instance:
        object = Range(**object_values) # IGNORE:W0142
        object.statement = self
        return object
    
    def _locate_object(self):
        Range = self.predicate.Range # IGNORE:E1101
        if not Range:
            return None
        object = self.object_resource
        if Resource == Range:
            pass 
        elif object:
            object = Range.objects.get(resource=object)
        else:
            object = Range.objects.get(statement=self)
        return object
    
    
# Literals
    

class Boolean(Model, Literal):

    statement = ForeignKey(Statement, unique=True)
    value = BooleanField()


class Date(Model, Literal):

    statement = ForeignKey(Statement, unique=True)
    value = DateField()


class Time(Model, Literal): 

    statement = ForeignKey(Statement, unique=True)
    value = DateTimeField()


class Duration(Model, Literal): 

    statement = ForeignKey(Statement, unique=True)
    start = DateTimeField()
    end = DateTimeField()
    
    def __getvalue(self):
        return self.start, self.end
    def __setvalue(self, values):
        self.start, self.end = values
    value = property()
    

class Decimal(Model, Literal):

    statement = ForeignKey(Statement, unique=True)
    value = DecimalField(max_digits=18, decimal_places=2)


class Float(Model, Literal):
    
    statement = ForeignKey(Statement, unique=True)
    value = FloatField()
    

class Email(Model, Literal):

    statement = ForeignKey(Statement, unique=True)
    value = EmailField()


class String(Model, Literal):

    statement = ForeignKey(Statement, unique=True)
    value = TextField()
    language = CharField(max_length=15, default='en-US')

    def __unicode__(self):
        return self.value

    def __eq__(self, other):
        return self.value == unicode(other)

    def __hash__(self):
        return hash(self.value)


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
