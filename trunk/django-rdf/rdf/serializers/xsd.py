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
        from _xsd import _Deserializer
        _DFacade.__init__(self, # IGNORE:W0142
            _Deserializer(ontology_path, **options), # IGNORE:W0142 
            ontology_path, 
            **options)

