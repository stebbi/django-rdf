"""
This command uses model reflection to synthesize RDF ontology fragments. 

It is automatically invoked from the syncvb command. This sequence first loads 
the core ontology fragments (RDF, RDF Schema...), then synthesizes additional 
fragments from installed Django applications using the directives in 

    settings.RDF_MAPPING, 

and finally loads the entire set of remaining ontology fragments, including the 
synthesized ones.
"""

import codecs, optparse, os, sys, traceback

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import AutoField, BooleanField, CharField, DateField, \
    DateTimeField, DecimalField, FloatField, IntegerField, TextField, TimeField, \
    get_apps, get_models
from django.db.models.fields.related import RelatedField
from django.template import Context, loader

from rdf.models import Cardinality, Concept, Namespace, Resource
from rdf.shortcuts import get, get_or_create


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        optparse.make_option('--verbosity', 
            action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
    )

    help = 'Mirrors one or more apps into ontology fragments in RDF format.'
    args = "[...]"

    def __init__(self):
        BaseCommand.__init__(self)
        self.verbosity, self.show_traceback, self.fail_gracefully = 1, False, False
        self._fragments, self._concept_cache = [], {}

    def handle(self, *labels, **options): # IGNORE:W0613
        self.verbosity = int(options.get('verbosity', 1))
        self.show_traceback = options.get('traceback', False)
        self.fail_gracefully = options.get('graceful', False)
        
        if hasattr(settings, 'RDF_MAPPING'):
            self._mirror_apps()
            self._generate_RDF()
        
    def _mirror_apps(self):
        try: 
            for app in get_apps():
                app_path = u'.'.join(app.__name__.split('.')[:-1])
                if not settings.RDF_MAPPING.has_key(app_path):
                    continue # Skip this app, it's not mapped
                f = FragmentData(app, app_path, settings.RDF_MAPPING[app_path])
                self._fragments.append(f)
            # First pass to create every available concept:
            for f in self._fragments:
                self._concept_cache.update(f.mirror_concepts())
            # Second pass with all available concepts cached to provide ranges:
            for f in self._fragments: 
                f.mirror_predicates(self._concept_cache)
        except Exception, x: # IGNORE:W0703 Catching everything
            if 0 < self.verbosity:
                print '''Mirroring failed with an exception.'''
            if self.show_traceback:
                exc = sys.exc_info()
                print x, type(x)
                traceback.print_tb(exc[2])

        if 0 < self.verbosity:
            nconc, npred = 0, 0
            for f in self._fragments:
                nconc += len(f.concepts)
                npred += len(f.predicates) 
            print 'Created %s ontology fragments (%s concepts, %s predicates)' \
                % (len(self._fragments), nconc, npred)
                    
    def _generate_RDF(self):
        try:
            for f in self._fragments:
                dirname = os.path.join(os.path.dirname(f.app.__file__), 'ontology') 
                if not os.path.exists(dirname):
                    os.mkdir(dirname)
                basename = f.app_path.replace('.', '-') + '.rdf'
                of = codecs.open(os.path.join(dirname, basename), 'w', encoding='utf-8')
                of.write(generate_RDF(f))
                of.close()
        except Exception, x: # IGNORE:W0703 Catching everything
            if 0 < self.verbosity:
                print '''RDF generation failed failed with an exception.'''
            if self.show_traceback:
                exc = sys.exc_info()
                print x, type(x)
                traceback.print_tb(exc[2])
            
            
XS, DRDFS = get((Namespace, 'xs'), (Namespace, 'drdfs')) 
    
_LITERAL_TYPE_MAP = {
    AutoField: XS['decimal'],
    BooleanField: XS['boolean'],
    CharField: XS['string'],
    DateField: XS['date'], 
    DateTimeField: XS['time'],
    DecimalField: XS['decimal'], 
    FloatField: XS['float'],  
    IntegerField: XS['decimal'], 
    TextField: XS['string'], 
    TimeField: XS['time'],
}


class FragmentData(object):
    
    def __init__(self, app, app_path, mapping):
        self.app, self.app_path, self.mapping = app, app_path, mapping
        try: 
            self.namespace = Namespace.objects.get(resource__name=mapping['namespace'])
        except Namespace.DoesNotExist:
            app_label = self.app_path.split('.')[-1]
            self.namespace, _ = get_or_create(Namespace, app_label, mapping['namespace'])
        self.concepts, self.predicates = {}, {} 
        self._concept_cache = None
        self._object_names = [_.strip() for _ in mapping['models'].split(',')] \
            if mapping.has_key('models') else None
            
    def mirror_concepts(self):
        for Model in get_models(self.app):
            if self._object_names is None \
                or Model._meta.object_name in self._object_names:
                model_name, concept = self._mirror_concept(Model)
                self.concepts[model_name] = concept
        return self.concepts

    def _mirror_concept(self, Model): # IGNORE:W0613
        name = Model._meta.object_name # IGNORE:W0212
        model_name = u'.'.join((self.app.__name__, name))
        concept = ConceptData(
            namespace=self.namespace, 
            name=name,
            title=Model._meta.verbose_name, # IGNORE:W0212
            description=u'Synthesized from %s' % model_name, 
            model_name=model_name)
        return model_name, concept
        
    def mirror_predicates(self, all_concepts):
        self._concept_cache = all_concepts
        for Model in get_models(self.app):
            for field in Model._meta.fields: # IGNORE:W0212
                self._mirror_predicate(Model, field)
            
    def _mirror_predicate(self, Model, field):
        model_name = u'.'.join((self.app.__name__, Model._meta.object_name)) # IGNORE:W0212
        try:
            concept = self.concepts[model_name]
        except KeyError:
            return 
        # Use the name, not the attname - otherwise the query compiler will break:
        field_name = u'.'.join((model_name, field.name))
        if 'resource' == field_name and type(field) == Resource:
            return
        values = PredicateData(
            namespace=self.namespace, 
            name=u'_'.join((Model._meta.object_name, field.name)), # IGNORE:W0212
            domain=concept, 
            title=u' '.join((Model._meta.object_name, field.name)), # IGNORE:W0212
            description=u'Synthesized from %s' % field_name, 
            field_name=field_name)
        range_values = self._resource_range_values(Model, field) \
            if isinstance(field, RelatedField) else \
            _literal_range_values(Model, field)
        values.__dict__.update(range_values)
        self.predicates[field_name] = values
        
    def _resource_range_values(self, Model, field): # IGNORE:W0613
        range_name = u'.'.join((field.rel.to.__module__, field.rel.to.__name__))
        range = None
        try:
            # Includes local concepts as well as concepts from the other apps:
            range = self._concept_cache[range_name]
        except KeyError:
            # Failed - try the installed ontology instead?
            # This requires an exact one-to-one concept-modelname match:
            range = Concept.objects.get(model_name=range_name)
        cardinality = Cardinality.objects.get(
            domain=('?' if field.unique else '*'), # ? and *, not 1 and + 
            range=('?' if field.null else '1'))
        return dict(
            range=range,
            cardinality=cardinality,
            literal=False)
        
def _literal_range_values(Model, field): # IGNORE:W0613
    range = _LITERAL_TYPE_MAP[type(field)]
    cardinality = Cardinality.objects.get(
        domain=('1' if field.unique else '+'), # 1 and +, not ? and *
        range=('?' if field.null else '1'))
    return dict(
        range=range,
        cardinality=cardinality,
        literal=True)


class ConceptData(object):
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            assert not value is None
            setattr(self, key, value)
            
    def __geturi(self):
        return self.namespace.uri + self.name # IGNORE:E1101
    uri = property(__geturi)        
    
            
class PredicateData(object):
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            assert not value is None
            setattr(self, key, value)

    def __geturi(self):
        return self.namespace.uri + self.name # IGNORE:E1101
    uri = property(__geturi)        
    
            
def generate_RDF(fragment):
    t = loader.get_template('internal/mirror.rdf')
    if fragment.mapping.has_key('title'):
        ontology_title = fragment.mapping['title']
    else:
        ontology_title = fragment.app_path
    if fragment.mapping.has_key('description'):
        ontology_description = fragment.mapping['description']
    else:
        ontology_description = 'Synthesized from %s.' % fragment.app_path
    return t.render(Context({
        'ontology_code': fragment.namespace.code, 
        'ontology_uri': fragment.namespace.uri, 
        'ontology_title': ontology_title, 
        'ontology_description': ontology_description, 
        'concepts': fragment.concepts, 
        'predicates': fragment.predicates}))

