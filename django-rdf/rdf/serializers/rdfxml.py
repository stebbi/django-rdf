'''
RDF ontology serialization/deserialization. 

This module is a facade that delegates the actual serialization to the _rdf module. 
This is an implementation trick that solves the following problem: Django loads all 
registered serialization modules before syncdb runs, which rules out module-level 
constructs that are loaded from the database. The _rdf module is not loaded until a
deserializer object is actually constructed, so it can use module-level objects of 
that kind. 
'''
from django.core.serializers import base

from rdf.serializers import _DFacade


class Serializer(base.Serializer):
    """
    Not implemented.
    """

    def start_serialization(self):
        raise base.SerializationError('RDF/XML serialization is not supported')

    def end_serialization(self):
        raise base.SerializationError('RDF/XML serialization is not supported')

    def start_object(self, obj):
        raise base.SerializationError('RDF/XML serialization is not supported')

    def getvalue(self):
        raise base.SerializationError('RDF/XML serialization is not supported')

    def handle_field(self, obj, field):
        raise base.SerializationError('RDF/XML serialization is not supported')

    def handle_fk_field(self, obj, field):
        raise base.SerializationError('RDF/XML serialization is not supported')

    def handle_m2m_field(self, obj, field):
        raise base.SerializationError('RDF/XML serialization is not supported')


class Deserializer(_DFacade):
    '''
    Facade that wraps the real deserializer.
    '''

    def __init__(self, ontology_path, **options):
        # Gets around the load-during-syncdb problem: 
        from _rdfxml import _Deserializer
        _DFacade.__init__(self,
            _Deserializer(ontology_path, **options),
            ontology_path,
            **options)

