import pdb


class Namespaces(object):
    
    def __init__(self):
        self._table = {}

    def has_key(self, key):
        return self._table.has_key(key)

    def __getitem__(self, key):
        assert isinstance(key, basestring)
        if not self._table.has_key(key):
            self._table[key] = NamespaceRef(code=key)
        return self._table[key]
    
    def __len__(self):
        return len(self._table)
    
    def __iter__(self):
        for v in self._table.values():
            yield v
    
    def __unicode__(self):
        return u'\n'.join(
            ['Namespaces:'] + \
            [unicode((key, unicode(value), unicode(value.binding))) \
            for key, value in self._table.items()])

    def __str__(self):
        return str(unicode(self))
    
    def _get_default(self):
        if not self._table.has_key(NamespaceRef.DEFAULT_CODE):
            self._table[NamespaceRef.DEFAULT_CODE] = \
                NamespaceRef(code=NamespaceRef.DEFAULT_CODE)
        return self._table[NamespaceRef.DEFAULT_CODE]
    DEFAULT = property(_get_default)

    def resolve(self):
        for n in self:
            n.resolve()
            

class Variables(object):
    
    def __init__(self):
        self._table = {}

    def add(self, *args):
        for variable in args:
            assert isinstance(variable, Variable)
            self[variable] # IGNORE:W0104

    def has_key(self, key):
        return self._table.has_key(key)

    def __getitem__(self, key):
        if isinstance(key, Variable):
            key, variable = key.name, key
        else:
            key, variable = key, Variable(name=key)
        assert isinstance(key, basestring) and isinstance(variable, Variable)
        if not self._table.has_key(key):
            self._table[key] = variable
        return self._table[key]
    
    def __delitem__(self, key):
        del self._table[key]
        
    def __len__(self):
        return len(self._table)
        
    def __iter__(self):
        for v in self._table.values():
            yield v

    def __unicode__(self):
        return u'\n'.join(
                ['Variables:'] + \
                [unicode((key, unicode(value), unicode(value.concept))) \
            for key, value in self._table.items()])

    def __str__(self):
        return str(unicode(self))

    def _get_default(self):
        if not self._table.has_key(Variable.DEFAULT_NAME):
            self._table[Variable.DEFAULT_NAME] = Variable(name=Variable.DEFAULT_NAME)
        return self._table[Variable.DEFAULT_NAME]
    DEFAULT = property(_get_default)
        

class Predicates(list):
    
    def __unicode__(self):
        return u'\n'.join(['Predicates:'] + [unicode(p) for p in self])

    def __str__(self):
        return str(unicode(self))


class Constraints(list):
    
    def __unicode__(self):
        return u'\n'.join(['Constraints:'] + [unicode(p) for p in self])

    def __str__(self):
        return str(unicode(self))


class Reference(object):
    
    def __init__(self):
        self.binding = None


class NamespaceRef(Reference):
    
    DEFAULT_CODE = '_'
    
    def __init__(self, code=None, uri=None, binding=None, position=None):
        """
        Supply either code and URI or a binding. If a binding is supplied the 
        code and URI parameters are ignored.
        """
        super(self.__class__, self).__init__()
        if binding is None:
            self.code = code
            self._uri = uri
            self.binding = None
        else:
            self.code = binding.code
            self._uri = binding.uri
            self.binding = binding
        self.position = position
        
    def _get_uri(self):
        return self._uri
    def _set_uri(self, uri):
        if self._uri is None or self._uri == uri:
            self._uri = uri
        else:
            raise Exception('attempted to reset %s to %s' % (unicode(self), uri))
    uri = property(_get_uri, _set_uri)
        
    def __unicode__(self):
        return self.code
    
    def __debug(self):
        return u'code: `%(code)s`, uri: `%(_uri)s` %(position)s' % self.__dict__

    def __str__(self):
        return str(unicode(self))
    

class ConceptRef(Reference):
    
    def __init__(self, name=None, namespace=None, binding=None, position=None):
        """
        Supply either a name and a namespace or a binding. If a binding is supplied
        then name and namespace parameters will be ignored.
        """
        super(self.__class__, self).__init__()
        if binding is None:
            assert not name is None
            self.name = name
            if namespace is not None:
                assert isinstance(namespace, NamespaceRef)
            self._namespace = namespace
            self.binding = None
        else:
            self.name = binding.name
            self.namespace = NamespaceRef(binding=binding.namespace)
            self.binding = binding
        self.position = position

    def _get_namespace(self):
        return self._namespace
    def _set_namespace(self, namespace):
        assert isinstance(namespace, NamespaceRef)
        self._namespace = namespace
    namespace = property(_get_namespace, _set_namespace)
    
    def _get_code(self):
        assert not self.namespace is None and not self.name is None
        return u':'.join((unicode(self.namespace), self.name))
    code = property(_get_code)
    
    def __unicode__(self):
        return self.code if not self.position else \
            u'`%s` %s' % (self.code, self.position) 
    
    def __str__(self):
        return str(unicode(self))
    
    
class Variable(object):
    
    DEFAULT_NAME = '_'
    
    def __init__(self, name, concept=None, predicates=None, position=None):
        from rdf.models import Concept
        self.name = name
        if isinstance(concept, Concept):
            concept = ConceptRef(binding=concept)
        self._concept = concept
        self.predicates = predicates if not predicates is None else []
        self.position = position
        
    def _get_concept(self):
        return self._concept
    def _set_concept(self, concept):
        if self._concept is None or self._concept == concept:
            self._concept = concept
        else:
            raise Exception('attempted to reset %s to %s' % (unicode(self), concept))
    concept = property(_get_concept, _set_concept)

    def __unicode__(self):
        s = u'name: %(name)s, concept: {%(_concept)s}'
        if self.position:
            s += ' %(position)s'  
        return s % self.__dict__

    def __str__(self):
        return str(unicode(self))
    
    
class PredicateRef(Reference):
    
    def __init__(self, 
        name=None, namespace=None, variable=None, binding=None, position=None):
        """
        Supply either name and namespace, or binding. If a binding is supplied 
        then name and namespace parameters will be ignored.
        """
        super(self.__class__, self).__init__()
        self._variable = variable
        if binding is None:
            self.name = name
            self.namespace = namespace
            self.binding = None
        else:
            self.name = binding.name
            self.namespace = binding.namespace
            self.binding = binding
        self.position = position

    def _get_variable(self):
        return self._variable
    def _set_variable(self, variable):
        if self._variable is None or self._variable == variable:
            self._variable = variable
        else:
            raise Exception('attempted to reset %s to %s' % (unicode(self), variable))
    variable = property(_get_variable, _set_variable)

    def _get_code(self):
        if self.namespace is None:
            pdb.set_trace()
        return u':'.join((self.namespace.code, self.name))
    code = property(_get_code)
    
    def __unicode__(self):
        s = u'%s, variable: {%s}' % (self.code, self._variable)
        if self.position: 
            s += ', ' + unicode(self.position)
        return s
    
    def __str__(self):
        return str(unicode(self))


class Constraint(object):
    
    def __init__(self, subject, predicate, object, position=None):
        from rdf.models import Predicate
        self.subject = subject
        if isinstance(predicate, PredicateRef):
            self.predicate = predicate
        elif isinstance(predicate, Predicate):
            self.predicate = PredicateRef(binding=predicate)
        assert isinstance(self.predicate, PredicateRef)
        self.object = object
        self.position = position
                
    def __unicode__(self):
        return u' '.join([unicode(i) for i in \
            (self.subject, self.predicate, self.object, self.position)])
    
    def __str__(self):
        return str(unicode(self))



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
