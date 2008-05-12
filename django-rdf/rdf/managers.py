import re

from django.db.models import Model, Manager

from rdf.query.query import SPARQLQuerySet


_WHITESPACE = re.compile('\s+')
_DEFAULT_OFFSET = 0
_DEFAULT_LIMIT = 100 


class RDFManager(Manager):
    
    def get_query_set(self):
        return SPARQLQuerySet(self.model)
    

class ResourceManager(RDFManager):

    def parameterize(self, *args, **kwargs): # IGNORE:R0201
        """
        A filter for constructing keyword arguments for passing to the model constructor
        or the create or get_or_create methods of this manager.

        The arguments are processed and new keyword arguments added to the keyword
        arguments received. The resulting keyword arguments dictionary is returned.

        The keyword arguments received must not conflict with the new keyword
        arguments formed.

        The argument list should be formed as follows:

            0 arguments: No keyword arguments added.

            1 argument:  Added as the 'name' element of the returned dict.

            2 arguments:
                Argument 0: Added as the 'namespace' element.
                Argument 1: Added as the 'name' element.

            3 arguments:
                Argument 0: Added as the 'namespace' element.
                Argument 1: Added as the 'name' element.
                Argument 2: Added as the 'type' element.

        If more than 3 arguments are passed an exception is raised.
        """
        from rdf.models import Namespace
        RDFS = Namespace.objects.RDFS
        l = len(args)
        if 0 == l:
            pass
        elif 1 == l:
            assert not kwargs.has_key('name')
            kwargs['name'] = args[0]
            if not kwargs.has_key('type'):
                kwargs['type'] = RDFS['Resource']
        elif 2 == l:
            assert not kwargs.has_key('name') and not kwargs.has_key('namespace')
            kwargs['namespace'], kwargs['name'] = args[0], args[1]
            if not kwargs.has_key('type'):
                kwargs['type'] = RDFS['Resource']
        elif 3 == l:
            assert not kwargs.has_key('name') \
                and not kwargs.has_key('namespace') \
                and not kwargs.has_key('type')
            kwargs['namespace'] = args[0]
            kwargs['name']= args[1]
            kwargs['type'] = args[2]
        else:
            raise Exception('expected 3 or fewer arguments, got %s' % unicode(args))
        return kwargs


class NamespaceManager(RDFManager):

    def __getRDF(self):
        if not hasattr(self, '_NamespaceManager__RDF'):
            self.__RDF = self.get(code='rdf') # IGNORE:W0201
        return self.__RDF
    RDF = property(__getRDF)

    def __getRDFS(self):
        if not hasattr(self, '_NamespaceManager__RDFS'):
            self.__RDFS= self.get(code='rdfs') # IGNORE:W0201
        return self.__RDFS
    RDFS = property(__getRDFS)

    def __gettype(self):
        if not hasattr(self, '_NamespaceManager__type'):
            self.__type = self.RDFS['Namespace'] # IGNORE:W0201
        return self.__type
    type = property(__gettype)

    def parameterize(self, *args, **kwargs): # IGNORE:R0201
        """
        A filter for constructing keyword arguments for passing to the model constructor
        or the create or get_or_create methods of this manager.

        The arguments are processed and new keyword arguments added to the keyword
        arguments received. The resulting keyword arguments dictionary is returned.

        The keyword arguments received must not conflict with the new keyword
        arguments formed.

        The argument list should be formed as follows:

            0 arguments: No keyword arguments added.

            1 argument:  Added as the 'code' element of the returned dict.

            2 arguments:
                Argument 0: Added as the 'code' element.
                Argument 1: Added as the 'resource' element.

        If more than 2 arguments are passed an exception is raised.
        """
        from rdf.models import Namespace, Resource
        from rdf.shortcuts import get_or_create
        l = len(args)
        if 0 == l:
            pass
        elif 1 == l:
            kwargs['code'] = args[0]
        elif 2 == l:
            r = args[1]
            r, _ = (r, False) if not isinstance(r, basestring) else \
                get_or_create(Resource, r, type=Namespace.objects.RDFS['Namespace'])
            kwargs['code'], kwargs['resource'] = args[0], r
        else:
            raise Exception(
                '''expected namespace code and resource, got '%s' ''' % unicode(args))
        return kwargs


class OntologyManager(Manager):
    
    def __init__(self):
        super(OntologyManager, self).__init__()
        self._concept = None
    
    def __getconcept(self):
        if self._concept is None:
            from rdf.models import Concept
            self._concept = Concept.objects.get(
                resource__namespace__code='owl', resource__name='Ontology')
        return self._concept
    concept = property(__getconcept)


class ConceptManager(RDFManager):

    DEFAULT_MODEL_NAME = 'rdf.models.Resource'

    def __gettype(self):
        if not hasattr(self, '_ConceptManager__type'):
            from rdf.models import Namespace
            self.__type = Namespace.objects.RDFS['Class'] # IGNORE:W0201
        return self.__type
    type = property(__gettype)
    
    def values_for_concept(self, concept, predicates=None, mangle=False):
        if predicates is None:
            predicates = concept.mandatory_literals
        rdql = self._rdql(domain=concept, predicates=predicates)
        return self.get_query_set().rdql(rdql, mangle=mangle).filter()
    
    def values_for_predicates(self, *predicates, **kwargs):
        mangle = kwargs['mangle'] if kwargs.has_key('mangle') else False
        rdql = self._rdql(domain=kwargs['domain'], predicates=predicates)
        return self.get_query_set().rdql(rdql, mangle=mangle).filter()
        
    def _rdql(self, domain, predicates):
        namespaces = {domain.namespace.code: domain.namespace}
        for p in predicates:
            namespaces[p.namespace.code] = p.namespace
        select = 'select %s ' % u', '.join(['c.' + p.code for p in predicates])
        tables = 'from %s c ' % domain.code
        using =  'using ' + u', '.join(
            ['%s for "%s"' % (n.code, n.uri) for _, n in namespaces.items()])
        return select + tables + using
    
    def parameterize(self, *args, **kwargs): # IGNORE:R0201
        """
        A filter for constructing keyword arguments for passing to the model constructor
        or the create or get_or_create methods of this manager.

        The arguments are processed and new keyword arguments added to the keyword
        arguments received. The resulting keyword arguments dictionary is returned.

        The keyword arguments received must not conflict with the new keyword
        arguments formed.

        The argument list should be formed as follows:

            0 arguments: Exception raised. A 'resource' element is required.

            1 argument:  Added as the 'resource' element of the returned dict.

            2 arguments: Used to get or create a resource used as the 'resource' element.
                Argument 0: The resource namespace.
                Argument 1: The resource name.

            3 arguments:
                Argument 0, 1: See description for 2 arguments.
                Argument 2: Becomes the 'model_name' parameter.

        If a 'name' keyword argument is not provided, then the name of the 'resource'
        keyword argument (after parameterizing) is used for the 'name'.

        If more than 3 arguments are passed an exception is raised.

        Note that passing 2 or more arguments may result in the creation of an instance
        of the Resource model, and a corresponding database INSERT. This needs reworking.
        """
        from rdf.models import Namespace, Resource, Concept
        l = len(args)
        if 0 == l:
            raise Exception('missing arguments, got %s, %s' % (args, kwargs))
        elif 1 == l:
            kwargs['resource'] = args[0]
        elif 2 == l:
            CLASS = Concept.objects.get(
                resource__namespace=Namespace.objects.RDFS, resource__name='Class')
            kwargs['resource'], _ = Resource.objects.get_or_create(
                namespace=args[0], name=args[1], defaults=dict(type=CLASS))
        elif 3 == l:
            CLASS = Concept.objects.get(
                resource__namespace=Namespace.objects.RDFS, resource__name='Class')
            kwargs['resource'], _ = Resource.objects.get_or_create(
                namespace=args[0], name=args[1], defaults=dict(type=CLASS))
            kwargs['model_name'] = args[2]
        else:
            raise Exception(
                'expected resource or namespace and name, and optionally a model name; got %s' \
                % args)
        return kwargs


class PredicateManager(RDFManager):

    def __gettype(self):
        if not hasattr(self, '_PredicateManager__type'):
            from rdf.models import Namespace, Concept
            RDF = Namespace.objects.RDF
            self.__type = Concept.objects.get(resource=RDF['Property']) # IGNORE:W0201
        return self.__type
    type = property(__gettype)

    def parameterize(self, *args, **kwargs): # IGNORE:R0201
        """
        A filter for constructing keyword arguments for passing to the model constructor
        or the create or get_or_create methods of this manager.

        The arguments are processed and new keyword arguments added to the keyword
        arguments received. The resulting keyword arguments dictionary is returned.

        The keyword arguments received must not conflict with the new keyword
        arguments formed.

        The argument list should be formed as follows:

            0 arguments: No keyword arguments added.

            1 argument:  Added as the 'name' element of the returned dict.

            2 arguments: Raises Exception.

            3 arguments:
                'resource': a Resource formed from arguments 0, 1 using get_or_create.
                'name': argument 1 becomes the predicate name.
                XXX Cleanup?

        If 2 or more than 3 arguments are passed an exception is raised.
        """
        from rdf.models import Namespace, Resource, Concept
        from rdf.shortcuts import get_or_create
        l = len(args)
        if 0 == l:
            pass
        elif 1 == l:
            kwargs['resource'] = args[0]
        elif 2 == l:
            PROPERTY = Concept.objects.get(
                resource__namespace=Namespace.objects.RDF, resource__name='Property')
            kwargs['resource'], _ = get_or_create(
                Resource, namespace=args[0], name=args[1], type=PROPERTY)
        elif 3 == l:
            PROPERTY = Concept.objects.get(
                resource__namespace=Namespace.objects.RDF, resource__name='Property')
            kwargs['resource'], _ = get_or_create(
                Resource, namespace=args[0], name=args[1], type=PROPERTY)
            kwargs.update(args[2]) 
        else:
            raise Exception('unexpected arguments (%s, %s)' \
                % (unicode(args), unicode(kwargs)))
        return kwargs


class StatementManager(RDFManager):

    def __gettype(self):
        if not hasattr(self, '_StatementManager__type'):
            from rdf.models import Namespace, Concept
            RDFS = Namespace.objects.RDFS
            self.__type = Concept.objects.get(resource=RDFS['Statement']) # IGNORE:W0201
        return self.__type
    type = property(__gettype)

    def create(self, **kwargs): 
        return super(self.__class__, self).create(**self.__filterkwargs(**kwargs)) # IGNORE:W0142

    def get(self, *args, **kwargs):
        kwargs = self.__filterkwargs(True, **kwargs) # IGNORE:W0142
        return super(self.__class__, self).get(*args, **kwargs) # IGNORE:W0142

    def get_or_create(self, **kwargs): 
        # XXX Invokes __filterkwargs twice... clean up.
        assert len(kwargs), 'get_or_create() must be passed at least one keyword argument'
        defaults = kwargs.pop('defaults', {})
        try:
            return self.get(**kwargs), False # IGNORE:W0142
        except self.model.DoesNotExist:
            kwargs = self.__filterkwargs(False, **kwargs) # IGNORE:W0142
            params = dict([(k, v) for k, v in kwargs.items() if '__' not in k])
            params.update(defaults)
            obj = self.model(**params) # IGNORE:W0142
            obj.save()
            return obj, True

    def __filterkwargs(self, objectconstraints=False, **kwargs): 
        from rdf.models import Predicate, Resource
        if kwargs.has_key('subject'):
            s = Predicate.locate_resource(kwargs['subject'])
            if s is None:
                raise Exception('subject (%s) has no resource field' % unicode(kwargs['subject']))
            else:
                kwargs['subject'] = s
        k = 'object'
        if kwargs.has_key(k):
            # XXX This is dirty...
            # Also overlaps with parts of Statement and Predicate.
            v = kwargs[k]
            if v is not None:
                if isinstance(v, Resource):
                    del kwargs[k]
                    kwargs['object_resource'] = v
                elif isinstance(v, Model) and hasattr(v, 'resource'):
                    del kwargs[k]
                    kwargs['object_resource'] = v.resource
                elif objectconstraints:
                    del kwargs[k]
                    p = kwargs['predicate']
                    reverse = p.Range.__name__.lower()
                    if isinstance(v, dict):
                        for vk, vv in v.items():
                            kwargs['__'.join((reverse, vk, 'exact'))] = vv
                    else:
                        kwargs[reverse + '__value__exact'] = v
        return kwargs

    def parameterize(self, *args, **kwargs): # IGNORE:R0201
        """
        A filter for constructing keyword arguments for passing to the model constructor
        or the create or get_or_create methods of this manager.

        The arguments are processed and new keyword arguments added to the keyword
        arguments received. The resulting keyword arguments dictionary is returned.

        The keyword arguments received must not conflict with the new keyword
        arguments formed.

        The argument list should be formed as follows:

            0 or 1 arguments: Exception raised, subject and predicate are required.

            2 arguments:
                Argument 0: Added as the 'subject' element.
                Argument 1: Added as the 'predicate' element.

            3 arguments:
                Arguments 0, 1 - as for 2 arguments.
                Argument 3: Added as the 'object' element.

        If more than 3 arguments are passed an exception is raised.
        """
        from rdf.models import Predicate, Resource
        from rdf.shortcuts import get
        l = len(args)
        if 0 == l:
            pass # Using keyword arguments
        elif 1 == l:
            raise Exception('expect subject and predicate, and optionally object')
        elif 2 == l:
            p = args[1]
            p = get(Predicate, resource=p) if isinstance(p, Resource) else p
            kwargs['predicate'] = p
            kwargs['subject'] = args[0]
        elif 3 == l:
            p = args[1]
            p = get(Predicate, resource=p) if isinstance(p, Resource) else p
            kwargs['predicate'] = p
            kwargs['subject'] = args[0]
            kwargs['object'] = args[2]
        else:
            raise Exception(
                '''expected subject and predicate, and optionally object; got '%s' '''\
                % unicode(args))
        return kwargs

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
