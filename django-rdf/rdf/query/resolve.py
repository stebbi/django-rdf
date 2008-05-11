'''
The resolver decorates symbol table entries with bindings to ontology elements.

Every namespace, concept and predicate entry is bound to the corresponding resource. 
There is no direct binding from a variable into the ontology.

After binding, the resolver implements support for generic concepts and predicates 
by synthesizing new variables, predicates and constraints that use only concepts 
and predicates that are mapped to specific database tables and columns - concepts 
and predicates that are stored in the rdf_resources and rdf_statements tables are 
altered by adding new constraints using the rdf:type, rdf:subject, rdf:predicate 
and rdf:object predicates, which are bound to specific columns in these two tables.
'''

from rdf.query.ast import ConceptRef, Constraint, PredicateRef, Variable
from rdf.shortcuts import get


class ResolverError(Exception):
    pass


class NoResolution(ResolverError):
    
    def __init__(self, reference, exception):
        super(self.__class__, self).__init__(
            'unable to resolve %s reference %s' \
            % (type(reference).__name__, unicode(reference)))
        self.reference = reference
        self.exception = exception


def resolve(ast):
    """
    First bind concept and predicate references to correspondoing ontology elements.
    
    Then synthesize (and bind) new RDQL clauses for generic concepts and predicates. 
    """ 
    ast = _bind(ast)
    ast = _span(ast)
    ast = _generalize(ast)
    return ast  
        
        
def _bind(ast):
    """
    Binds concept and predicate references to corresponding ontology elements.
    """
    
    from rdf.models import Namespace, Predicate, Concept
    
    def _namespace(reference):
        if not reference.binding is None:
            raise ResolverError()
        try:
            reference.binding = Namespace.objects.get(resource__name=reference.uri)
        except Namespace.DoesNotExist, x: # IGNORE:E1101
            raise NoResolution(reference, x)

    def _variable(reference):
        _concept(reference.concept)

    def _concept(reference):
        if not reference.binding is None:
            return
        try:
            if reference.namespace is None:
                reference.namespace = ast.namespaces['_']                
            reference.binding = Concept.objects.get(
                resource__name=reference.name, 
                resource__namespace=reference.namespace.binding)
        except Concept.DoesNotExist, x: # IGNORE:E1101
            raise NoResolution(reference, x)
        
    def _predicate(reference):
        """
        Make sure concepts are bound before attempting to bind predicates.
        
        The names of synthesized predicates are normally prefixed with the 
        name of the domain concept. For example, the code of the Airport concept
        would be named Airport.code and appear as ns:Airport_code when qualified.
        
        The query compiler accepts a shorthand notation that enables queries 
        using the syntax a.code, where the variable a is defined with 
        Airport a. 
        
        Hence, we need to first check for ns:Airport_code, then look for ns:code. 
        """
        if not reference.binding is None:
            return
        if reference.namespace is None:
            reference.namespace = ast.namespaces['_']
        try:
            try:  
                name = u'_'.join((reference.variable.concept.name, reference.name))
                reference.binding = Predicate.objects.get(
                    resource__name=name, 
                    resource__namespace=reference.namespace.binding)
            except Predicate.DoesNotExist: # IGNORE:E1101
                reference.binding = Predicate.objects.get(
                    resource__name=reference.name, 
                    resource__namespace=reference.namespace.binding)
        except Predicate.DoesNotExist, x: # IGNORE:E1101
            raise NoResolution(reference, x)
        
    def _constraint(reference):
        _variable(reference.subject)
        reference.predicate.variable = reference.subject
        _predicate(reference.predicate)
        if reference.predicate.binding.range.literal:
            pass
        elif isinstance(reference.object, ConceptRef):
            _concept(reference.object)
        else:
            _variable(reference.object)

    for n in ast.namespaces:
        _namespace(n)
    for v in ast.variables:
        _variable(v)
    for p in ast.predicates:
        _predicate(p)
    for p in ast.constraints:
        _constraint(p)
    return ast


def _span(ast):
    """
    Replaces spanning predicates with the span segments.
    
    Every spanning predicate in the select clause needs to be replaced with the final
    segment in the span, and variables and constraints added to connect. 
    
    Then, every constraint with a spanning predicate needs to be similarly replaced.
    
    Connecting variables are generated using a naming convention that combines the 
    name of the original variable, the name of the spanning predicate, and the 
    ordinal of the span segment. For example, if x.n:span might be replaced with 
    
        x__n__span__1.n:a2
        
    and the constraints
    
        x n:a0 x__n__span__0
        x__n__span__0 n:a1 x__n__span__1
        
    where n:span = n:a0 | n:a1 | n:a2.
    
    The replacements are hung onto the replaced constraints and predicates using a 
    '_spanned' attribute.
    """
    def _segment_variable(span, segment, i):
        _ = u'__'.join(
            (span.variable.name, span.binding.namespace.mangled, 
             span.binding.name, str(i)))
        return Variable(name=_, concept=segment.predicate.range)
    
    def _segments(start, span, segments, length, end=None):
        variables, constraints = [], []
        previous = start
        for s, i in zip(segments, range(0, length)):
            if s.predicate.literal:
                continue
            if i < length - 1 and not end is None:
                _ = end
            else:
                _ = _segment_variable(span, s, i)
            variables.append(_)
            constraints.append(
                Constraint(subject=previous, predicate=s.predicate, object=_))
            previous = _
        span._spanned = PredicateRef(
            binding=segments[len(segments)-1].predicate, 
            variable=variables[len(variables)-1])
        return variables, constraints        
    
    variables, constraints = [], []
    for p in ast.predicates:
        length = p.binding.segments.count()
        if 0 < length:
            vv, cc = _segments(p.variable, p, p.binding.segments, length)
            variables.extend(vv)
            constraints.extend(cc)
    for c in ast.constraints:
        p = c.predicate
        length = p.binding.segments.count()
        if 0 < length:
            vv, cc = _segments(c.subject, p, p.binding.segments, length, c.object)
            variables.extend(vv)
            c._spanned = cc
    ast.variables.add(*variables)
    ast.constraints.extend(constraints)
    return ast


def _generalize(ast):
    """
    Generic resources are stored as instances of the RDF Resource model, and 
    statements using generic predicates are stored as instances of the RDF 
    Statement model. In both cases query compilation is complicated by the need to 
    insert additional variables, predicates and constraints to ensure that the 
    generated SQL uses the internal RDF tables where necessary.
    
    The generated RDQL clauses are full of names with excessive uses of `__`, 
    which is necessary to avoid name collisions - but also precludes the use of 
    the `__` substring in regular names (or else the possibility of name collisions
    arises again...).

    The generalizer is required not to modify the AST except by adding new elements. 
    In some cases predicates and constraints need to be replaced or expanded, which 
    is achieved by hanging new `_generalized` attributes on the existing objects.
    """ 
    
    from rdf.models import Namespace, Predicate, Concept

    RDF, RDFS, DRDFS = get((Namespace, 'rdf'), (Namespace, 'rdfs'), (Namespace, 'drdfs'))
    TYPE, SUBJECT, PREDICATE, OBJECT, ABOUT, STATEMENT, RESOURCE, _ = get(
        # This doesn't work here:
        #     RDF['type', 'subject', 'predicate', 'object', 'about']
        # ... because the Namespace [] operator is disabled during template execution... 
        (Predicate, RDF, 'type'), 
        (Predicate, RDF, 'subject'),
        (Predicate, RDF, 'predicate'),
        (Predicate, RDF, 'object'),
        (Predicate, RDF, 'about'),
        (Concept, RDF, 'Statement'),
        (Concept, RDFS, 'Resource'),
        (Concept, RDFS, 'Class')) 
    
    def _variable(reference):
        """
        Code generation for a generic concept needs to use the RDF model tables.
        This method ensures that the resources are constrained to the appropriate 
        concept, by synthesizing a new constraint of the form
        
            x rdf:type 10
 
        where 10 is the type_id column value for the resources x.
 
        It also points the code generator at the general resources table by 
        rebinding the input variable to the top-level resource concept. 
        """ 
        reference.concept.binding._generalized = RESOURCE
        pref = PredicateRef(variable=reference, binding=TYPE)
        ccon = Constraint(
            subject=reference, predicate=pref, object=reference.concept.binding.id)
        return (ccon,)
    
    def _predicate(reference):
        """
        Code generation for a generic predicate needs to use the RDF model tables. 
        This method takes a predicate reference from RDQL clauses of the kind 
            
            select x.y:z from y:X x using ...
            
        and creates new variables corresponding to implicit clauses of the kind
        
            rdf:Statement x__y__z__s
            <range of y:z> x__y__z__o
        
        Then three constraints are also added:
        
            x__y__z__s rdf:subject x
            x__y__z__s rdf:predicate y:z
            x__y__z__s rdf:object x__y__z__o

        """    
        assert not hasattr(reference, '_spanned')
        variables, constraints = [], []
        prefix = [
            reference.variable.name,            # x
            reference.binding.namespace.code,   # y
            reference.binding.name,             # z
        ]
        svar = Variable(
            name=u'__'.join(prefix + ['s']).replace('-', '_'), concept=STATEMENT)
        scon = Constraint(subject=svar, predicate=SUBJECT, object=reference.variable)
        pcon = Constraint(
            subject=svar, predicate=PREDICATE, object=reference.binding.id)
        ovar = Variable(
            name=u'__'.join(prefix + ['o']).replace('-', '_'), 
            concept=reference.binding.range)
        ocon = Constraint(subject=svar, predicate=OBJECT, object=ovar)
        if reference.binding.literal:
            if not reference.binding == ABOUT:
                # Must match identical construction in magic._compiler_support:
                opname = '_%s%svalue' \
                    % (reference.binding.range.namespace.code, 
                       reference.binding.range.name)
                opname.replace('-', '_')
                opred = Predicate.objects.get(
                    resource__name=opname, resource__namespace=DRDFS)
                opref = PredicateRef(binding=opred, variable=ovar)
            else:
                opref = reference # rdf:about is a special case...
        else:
            # Using rdf:about to indicate the URI of the resource. 
            # This is kind of broken in that the query will actually return the local 
            # name of the resource instead of the URI.
            opref = PredicateRef(binding=ABOUT, variable=ovar)
        assert not opref is None
        reference._generalized = opref
        variables.extend((svar, ovar))
        constraints.extend((scon, pcon, ocon))
        return variables, constraints

    def _constraint(reference):
        assert not hasattr(reference, '_spanned')
        variables = []
        prefix = [
            reference.predicate.variable.name,            # x
            reference.predicate.binding.namespace.code,   # y
            reference.predicate.binding.name,             # z
        ]
        svar = Variable(
            name=u'__'.join(prefix + ['s']).replace('-', '_'), concept=STATEMENT)
        scon = Constraint(
            subject=svar, predicate=SUBJECT, object=reference.predicate.variable)
        pcon = Constraint(
            subject=svar, predicate=PREDICATE, object=reference.predicate.binding.id)
        ocon = Constraint(subject=svar, predicate=OBJECT, object=reference.object)
        variables.append(svar)
        reference._generalized = (scon, pcon, ocon)
        return variables

    variables, constraints = [], []
    for v in ast.variables:
        if v.concept.binding.generic:
            constraints.extend(_variable(v))
    for p in ast.predicates:
        if hasattr(p, '_spanned'):
            p = p._spanned
        if p.binding.generic:
            vv, cc = _predicate(p)
            variables.extend(vv)
            constraints.extend(cc)
    for c in ast.constraints:
        if c.predicate.binding.generic:
            variables.extend(_constraint(c))
    ast.variables.add(*variables) # IGNORE:W0142
    ast.constraints.extend(constraints)
    return ast
    
