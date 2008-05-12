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
