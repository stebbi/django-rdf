from django.contrib.auth.models import ContentType, Permission, User
from django.test import Client

from rdf.models import \
    Namespace, Predicate, Resource, Statement, String, Concept, Cardinality
from rdf.query.query import SPARQLQuerySet 
from rdf.shortcuts import create, get, get_or_create
from rdf.testcase import TestCase


U = u'http://code.google.com/p/django-rdf/'


class TestResource(TestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.cw = create(Resource, name=U)

    def test_unicode(self):
        self.assertEqual(unicode(self.cw), U)

    def test_eq(self):
        self.assertNotEqual(self.cw, U)
        self.assertNotEqual(U, self.cw)

    def test_global_namespace(self):
        self.assertTrue(self.cw.namespace is None)

    def test_default_type(self):
        self.assertTrue(self.cw.type is None)

    def test_code(self):
        self.assertEqual(self.cw.code, U)

    def test_name(self):
        self.assertEqual(self.cw.name, U)

    def test_uri(self):
        self.assertEqual(self.cw.uri, U)
        self.assertEqual(U, self.cw.uri)

    def test_save(self):
        self.cw.save()
        r = Resource.objects.get(name=U)
        self.assertEqual(r, self.cw)


U1 = {
    'nsuri': U,         # Namespace URI
    'ns': u'ns',        # Namespace code
    'name': u'1',       # URI suffix
    'code': u'ns:1',    # URI code
    'uri': U + u'1'}    # complete URI (namespace URI + suffix)


class TestNamespace(TestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.cw = create(Resource, name=U)
        self.ns = create(Namespace, code=U1['ns'], resource=self.cw)
        self.cw1 = create(Resource, namespace=self.ns, name=U1['name'])

    def test_unicode(self):
        self.assertEqual(unicode(self.cw1), U1['code'])

    def test_eq(self):
        self.assertNotEqual(self.cw1, U1['uri'])
        self.assertNotEqual(U1['uri'], self.cw1)

    def test_namespace(self):
        self.assertEqual(self.cw1.namespace, self.ns)

    def test_name(self):
        self.assertEqual(self.cw1.name, U1['name'])

    def test_uri(self):
        self.assertEqual(self.ns.uri, U)
        self.assertEqual(self.cw1.uri, U1['uri'])

    def test_save(self):
        self.cw.save()
        self.ns.save()
        self.cw1.save()


class TestLiteral(TestCase):
    
    def test_check(self):
        XS = get(Namespace, 'xs')
        self.assertTrue(XS['string'].literal)
        self.assertTrue(XS['decimal'].literal)


class TestConcept(TestCase):

    def test_create(self):
        model_name = 'django.contrib.auth.models.User'
        N = create(Namespace, 'n', 'http://example.com/namespace/')
        T = create(Concept, N, 't', 'django.contrib.auth.models.User')
        self.assertEqual(N, T.namespace)
        self.assertEqual('t', T.name)
        self.assertEqual(model_name, T.model_name)
        from django.contrib.auth.models import User
        self.assertEqual(User, T.Model)

    def test_create_without_model_name(self):
        N = create(Namespace, 'n', 'http://example.com/namespace/')
        T = create(Concept, N, 't')
        self.assertEqual(N, T.namespace)
        self.assertEqual('t', T.name)
        self.assertEqual(Concept.objects.DEFAULT_MODEL_NAME, T.model_name)
        self.assertEqual(Resource, T.Model)

    def test_create_with_bad_model_name(self):
        N = create(Namespace, 'n', 'http://example.com/namespace/')
        f = lambda: create(Concept, N, 't', 'inexistent.model.Name')
        self.assertRaises(Exception, f)

    def test_resource_types(self):
        _, RDFS, OWL = get((Namespace, 'rdf'), (Namespace, 'rdfs'), (Namespace, 'owl'))
        CLASS, LITERAL, OWL_CLASS = RDFS['Class'], RDFS['Literal'], OWL['Class']
        types = Concept.objects.all()
        for t in types:
            if t.literal:
                # Nasty... special-casing the base literal type: 
                rtype = LITERAL
                if t is LITERAL:
                    rtype = CLASS
                self.assertEqual(rtype, t.resource.type)
            else:
                if not t.resource.type in (CLASS, OWL_CLASS):
                    print t.resource.type, t, t.resource
                self.assertTrue(t.resource.type in (CLASS, OWL_CLASS))

    def test_predicates(self):
        XS = get(Namespace, 'xs')
        TEXT = XS['string']
        mm = Cardinality.objects.get(domain='1', range='1')
        mo = Cardinality.objects.get(domain='1', range='?')
        oo = Cardinality.objects.get(domain='?', range='?')
        TMP = create(Namespace, 'tmp', 'http://tmp/tmp#')
        T = create(Concept, TMP, 'T')
        M0 = create(Predicate, TMP, 'M0', domain=T, range=TEXT, cardinality=mm) 
        M1 = create(Predicate, TMP, 'M1', domain=T, range=TEXT, cardinality=mm) 
        M2 = create(Predicate, TMP, 'M2', domain=T, range=TEXT, cardinality=mm)
        O0 = create(Predicate, TMP, 'O0', domain=T, range=TEXT, cardinality=mo) 
        O1 = create(Predicate, TMP, 'O1', domain=T, range=TEXT, cardinality=oo) 
        mandatory = T.mandatory_predicates 
        optional = T.optional_predicates
        all = T.predicates
        self.assertEqual(3, len(mandatory))
        self.assertEqual(2, len(optional))
        self.assertEqual(5, len(all))
        for M in (M0, M1, M2):
            self.assertTrue(M in mandatory)
            self.assertFalse(M in optional)
            self.assertTrue(M in all)
        for O in (O0, O1):
            self.assertFalse(O in mandatory)
            self.assertTrue(O in optional)
            self.assertTrue(O in all)
        for P in (M0, M1, M2, O0, O1):
            self.assertTrue(P in all)
            
    def test_mandatory(self):
        RDF, RDFS = get((Namespace, 'rdf'), (Namespace, 'rdfs'))
        pp = RDFS['Class'].mandatory_predicates
        self.assertTrue(RDF['type'] in pp)
        self.assertTrue(RDF['about'] in pp)
        

class TestPredicate(TestCase):

    def test_create_no_range(self):
        N = create(Namespace, 'n', 'http://example.com/namespace/')
        T = create(Concept, N, 't') 
        one_one = Cardinality.objects.get(domain='1', range='1') # IGNORE:E1101
        P = create(Predicate, N, 'p', domain=T, range=None, cardinality=one_one)
        self.assertEqual(N, P.namespace)
        self.assertEqual('p', P.name)
        self.assertEqual(N[P.name], P.resource)
        self.assertEqual(T, P.domain)
        self.assertEqual(None, P.range)

    def test_create_self_referential(self):
        N = create(Namespace, 'n', 'http://example.com/namespace/')
        T = create(Concept, N, 't')
        one_one = Cardinality.objects.get(domain='1', range='1') # IGNORE:E1101
        P = create(Predicate, N, 'p', domain=T, range=T, cardinality=one_one)
        self.assertEqual(N, P.namespace)
        self.assertEqual('p', P.name)
        self.assertEqual(N[P.name], P.resource)
        self.assertEqual(T, P.domain)
        self.assertEqual(T, P.range)


class TestStatement(TestCase):

    def test_create_no_object(self):
        N = create(Namespace, 'n', 'http://example.com/namespace/')
        T = create(Concept, N, 't')
        r = create(Resource, N, 'r', T)
        one_one = Cardinality.objects.get(domain='1', range='1') # IGNORE:E1101
        p = create(Predicate, N, 'p', domain=r.type, range=None, cardinality=one_one)
        s = create(Statement, r, p)
        self.assertEqual(r, s.subject)
        self.assertEqual(p, s.predicate)
        self.assertEqual(None, s.object)
        self.assertEqual(None, s.reified)

    def test_create_self_referential_on_Resource_model(self):
        N = create(Namespace, 'n', 'http://example.com/namespace/')
        T = create(Concept, N, 't')
        r = create(Resource, N, 'r', T)
        none_none = Cardinality.objects.get(domain='?', range='?') # IGNORE:E1101
        p = create(Predicate, N, 'p', domain=r.type, range=r.type, cardinality=none_none)
        s = create(Statement, r, p, r)
        self.assertEqual(r, s.subject)
        self.assertEqual(p, s.predicate)
        self.assertEqual(r, s.object)
        self.assertEqual(None, s.reified)

    def test_create_predicate_to_namespace(self):
        # Both Predicate and Namespace have resource fields.
        N = create(Namespace, 'n', 'http://example.com/namespace/')
        many_one = Cardinality.objects.get(domain='*', range='1') # IGNORE:E1101
        p = create(
            Predicate,
            N,
            'predicate-has-namespace',
            domain=Predicate.objects.type,
            range=Namespace.objects.type,
            cardinality=many_one)
        s = create(Statement, p, p, N)
        self.assertEqual(p, s.subject)
        self.assertEqual(p, s.predicate)
        self.assertEqual(N, s.object)
        self.assertEqual(None, s.reified)

    def test_create_from_values(self):
        N = create(Namespace, 'n', 'http://example.com/namespace/')
        T = create(Concept, N, 't')
        r = create(Resource, N, 'r', T)
        V = get(Namespace, code='xs')['string']
        one_none = Cardinality.objects.get(domain='1', range='?') # IGNORE:E1101
        p = create(Predicate, N, 'p', domain=r.type, range=V, cardinality=one_none)
        v = {'value': u'something clever'}
        s = create(Statement, r, p, v)
        self.assertEqual(r, s.subject)
        self.assertEqual(p, s.predicate)
        self.assertEqual(v['value'], s.object)
        self.assertEqual(String, type(s.object))
        self.assertEqual(None, s.reified)
        t = get(Statement, r, p)
        self.assertEqual(r, t.subject)
        self.assertEqual(p, t.predicate)
        self.assertEqual(v['value'], t.object)
        self.assertEqual(String, type(t.object))

    def test_get_or_create_from_values(self):
        N = create(Namespace, 'n', 'http://example.com/namespace/')
        T = create(Concept, N, 't')
        r = create(Resource, N, 'r', T)
        V = get(Namespace, code='xs')['string']
        one_none = Cardinality.objects.get(domain='1', range='?') # IGNORE:E1101
        p = create(Predicate, N, 'p', domain=r.type, range=V, cardinality=one_none)
        v = {'value': u'something clever'}
        s, _ = get_or_create(Statement, r, p, v)
        self.assertEqual(r, s.subject)
        self.assertEqual(p, s.predicate)
        self.assertEqual(v['value'], s.object)
        self.assertEqual(String, type(s.object))
        self.assertEqual(None, s.reified)
        t = get(Statement, r, p)
        self.assertEqual(r, t.subject)
        self.assertEqual(p, t.predicate)
        self.assertEqual(v['value'], t.object)
        self.assertEqual(String, type(t.object))

    def test_get_or_create_from_values_twice(self):
        N = create(Namespace, 'n', 'http://example.com/namespace/')
        T = create(Concept, N, 't')
        r = create(Resource, N, 'r', T)
        V = get(Namespace, code='xs')['string']
        one_none = Cardinality.objects.get(domain='1', range='?') # IGNORE:E1101
        p = create(Predicate, N, 'p', domain=r.type, range=V, cardinality=one_none)
        v = {'value': u'something clever'}
        s, _ = get_or_create(Statement, r, p, v)
        self.assertEqual(r, s.subject)
        self.assertEqual(p, s.predicate)
        self.assertEqual(v['value'], s.object)
        self.assertEqual(String, type(s.object))
        self.assertEqual(None, s.reified)
        t, _ = get_or_create(Statement, r, p)
        self.assertEqual(r, t.subject)
        self.assertEqual(p, t.predicate)
        self.assertEqual(v['value'], t.object)
        self.assertEqual(String, type(t.object))

    def test_get_from_values(self):
        N = create(Namespace, 'n', 'http://example.com/namespace/')
        T = create(Concept, N, 't')
        r = create(Resource, N, 'r', T)
        V = get(Namespace, code='xs')['string']
        one_none = Cardinality.objects.get(domain='1', range='?') # IGNORE:E1101
        p = create(Predicate, N, 'p', domain=r.type, range=V, cardinality=one_none)
        v = {'value': u'something clever'}
        s, _ = get_or_create(Statement, r, p, v)
        self.assertEqual(r, s.subject)
        self.assertEqual(p, s.predicate)
        self.assertEqual(v['value'], s.object)
        self.assertEqual(String, type(s.object))
        self.assertEqual(None, s.reified)
        t = get(Statement, r, p)
        self.assertEqual(r, t.subject)
        self.assertEqual(p, t.predicate)
        self.assertEqual(v['value'], t.object)
        self.assertEqual(String, type(t.object))


class TestShortcuts(TestCase):

    def test_get_namespace(self):
        RDFS, DCTERMS = get(Namespace, 'rdfs'), get(Namespace, 'dcterms')
        self.assertEqual(u'rdfs', RDFS.code)
        # self.assertEqual(get(URI, RDFS_URI_STR), rdfs.resource)
        # self.assertEqual(get(URI, DCTERMS_URI_STR), dcterms.resource)
        self.assertEqual('rdfs', RDFS.code)
        self.assertEqual('dcterms', DCTERMS.code)

    def test_predicate(self):
        p = get(Namespace, 'dc')['description']
        self.assertEqual(u'description', p.resource.name)
        self.assertEqual(u'description', p.name)
        self.assertEqual(p.domain, get(Namespace, 'rdfs')['Resource'])
        self.assertEqual(Resource, p.Domain)
        XS = get(Namespace, 'xs')
        STRING = XS['string']
        self.assertEqual(STRING, p.range)
        self.assertEqual(STRING.Model, String)
        self.assertEqual(String, p.Range)

    def test_statement(self):
        DESCRIPTION = u'''Description may include but is not limited to: an abstract,
        a table of contents, a graphical representation, or a free-text account of the resource.
        '''
        p = get(Namespace, 'dc')['description']
        s = create(Statement, p.resource, p, object={'value': DESCRIPTION, 'language': 'en-US'})
        t = get(Statement, p, p)
        self.assertEqual(p.name, 'description')
        self.assertEqual(s, t)
        self.assertEqual(s.subject, p.resource)
        self.assertEqual(s.object, DESCRIPTION)


class TestRDFS(TestCase):

    def test_ontology(self):
        RDFS = get(Namespace, 'rdfs')
        self.assertEqual(RDFS.code, u'rdfs')


class TestSPARQLQuerySet(TestCase):

    def test_simple_empty_with_literal_object(self):
        XS = get(Namespace, 'xs')
        TMP = create(Namespace, 'tmp', 'http://tmp/tmp#')
        TEXT = XS['string']
        self.assertTrue(TEXT.literal)
        C = create(Concept, TMP, 'C') # Defaults to 'rdf.models.Resource'
        one_one = Cardinality.objects.get(domain='1', range='1') # IGNORE:E1101
        P = create(Predicate, TMP, 'P', domain=C, range=TEXT, cardinality=one_one)
        self.assertTrue(P.literal)
        rqs = SPARQLQuerySet().rdql(\
            u'select c.tmp:P from tmp:C c using tmp for "http://tmp/tmp#"')
        select = u'''select c__tmp__P__o.value from rdf_resource c, rdf_statement c__tmp__P__s, rdf_string c__tmp__P__o where c.type_id = %s and c__tmp__P__s.subject_id = c.id and c__tmp__P__s.predicate_id = %s and c__tmp__P__s.id = c__tmp__P__o.statement_id''' % (C.id, P.id)
        count = u'''select count(*) from rdf_resource c, rdf_statement c__tmp__P__s, rdf_string c__tmp__P__o where c.type_id = %s and c__tmp__P__s.subject_id = c.id and c__tmp__P__s.predicate_id = %s and c__tmp__P__s.id = c__tmp__P__o.statement_id''' % (C.id, P.id)
        self.assertEqual(0, rqs.count())
        self.assertEqual(getattr(rqs, '_cached_query').select, select)
        self.assertEqual(getattr(rqs, '_cached_query').count, count)
        self.assertEqual(0, len(rqs.filter())) # IGNORE:E1101
    
    def test_simple_empty_with_resource_object(self):
        TMP = create(Namespace, 'tmp', 'http://tmp/tmp#')
        C, D = create((Concept, TMP, 'C'), (Concept, TMP, 'D'))
        one_one = Cardinality.objects.get(domain='1', range='1') # IGNORE:E1101
        P = create(Predicate, TMP, 'P', domain=C, range=D, cardinality=one_one)
        self.assertFalse(P.literal)
        rqs = SPARQLQuerySet().rdql(\
            u'select c.tmp:P from tmp:C c using tmp for "http://tmp/tmp#"')
        select = u'''select c__tmp__P__o.name from rdf_resource c, rdf_statement c__tmp__P__s, rdf_resource c__tmp__P__o where c.type_id = %s and c__tmp__P__s.subject_id = c.id and c__tmp__P__s.predicate_id = %s and c__tmp__P__s.object_resource_id = c__tmp__P__o.id''' % (C.id, P.id)
        count = u'''select count(*) from rdf_resource c, rdf_statement c__tmp__P__s, rdf_resource c__tmp__P__o where c.type_id = %s and c__tmp__P__s.subject_id = c.id and c__tmp__P__s.predicate_id = %s and c__tmp__P__s.object_resource_id = c__tmp__P__o.id''' % (C.id, P.id)
        self.assertEqual(0, rqs.count())
        self.assertEqual(getattr(rqs, '_cached_query').select, select)
        self.assertEqual(getattr(rqs, '_cached_query').count, count)
        self.assertEqual(0, len(rqs.filter())) # IGNORE:E1101
    
    def test_simple_empty_self_referential(self):
        TMP = create(Namespace, 'tmp', 'http://tmp/tmp#')
        C = create(Concept, TMP, 'C')
        one_one = Cardinality.objects.get(domain='1', range='1') # IGNORE:E1101
        P = create(Predicate, TMP, 'P', domain=C, range=C, cardinality=one_one)
        self.assertFalse(P.literal)
        rqs = SPARQLQuerySet().rdql(\
            u'select c.tmp:P from tmp:C c using tmp for "http://tmp/tmp#"')
        select = u'''select c__tmp__P__o.name from rdf_resource c, rdf_statement c__tmp__P__s, rdf_resource c__tmp__P__o where c.type_id = %s and c__tmp__P__s.subject_id = c.id and c__tmp__P__s.predicate_id = %s and c__tmp__P__s.object_resource_id = c__tmp__P__o.id''' % (C.id, P.id)
        count = u'''select count(*) from rdf_resource c, rdf_statement c__tmp__P__s, rdf_resource c__tmp__P__o where c.type_id = %s and c__tmp__P__s.subject_id = c.id and c__tmp__P__s.predicate_id = %s and c__tmp__P__s.object_resource_id = c__tmp__P__o.id''' % (C.id, P.id)
        self.assertEqual(0, rqs.count())
        self.assertEqual(getattr(rqs, '_cached_query').select, select)
        self.assertEqual(getattr(rqs, '_cached_query').count, count)
        self.assertEqual(0, len(rqs.filter())) # IGNORE:E1101
    
    def test_empty_chain_length_2(self):
        TMP = create(Namespace, 'tmp', 'http://tmp/tmp#')
        C, D, E = create((Concept, TMP, 'C'), (Concept, TMP, 'D'), (Concept, TMP, 'E'))
        one_one = Cardinality.objects.get(domain='1', range='1') # IGNORE:E1101
        P = create(Predicate, TMP, 'P', domain=C, range=D, cardinality=one_one)
        Q = create(Predicate, TMP, 'Q', domain=D, range=E, cardinality=one_one)
        rqs = SPARQLQuerySet().rdql(u'''
            select c.rdf:about, e.rdf:about 
            from tmp:C c, tmp:D d, tmp:E e
            where c tmp:P d
              and d tmp:Q e 
            using tmp for "http://tmp/tmp#",
                  rdf for "http://www.w3.org/1999/02/22-rdf-syntax-ns#"''')
        select = u'select c.name, e.name from rdf_resource c, rdf_statement c__tmp__P__s, rdf_resource e, rdf_resource d, rdf_statement d__tmp__Q__s where c__tmp__P__s.subject_id = c.id and c__tmp__P__s.predicate_id = %s and c__tmp__P__s.object_resource_id = d.id and d__tmp__Q__s.subject_id = d.id and d__tmp__Q__s.predicate_id = %s and d__tmp__Q__s.object_resource_id = e.id and c.type_id = %s and e.type_id = %s and d.type_id = %s' % (P.id, Q.id, C.id, E.id, D.id)
        count = u'select count(*) from rdf_resource c, rdf_statement c__tmp__P__s, rdf_resource e, rdf_resource d, rdf_statement d__tmp__Q__s where c__tmp__P__s.subject_id = c.id and c__tmp__P__s.predicate_id = %s and c__tmp__P__s.object_resource_id = d.id and d__tmp__Q__s.subject_id = d.id and d__tmp__Q__s.predicate_id = %s and d__tmp__Q__s.object_resource_id = e.id and c.type_id = %s and e.type_id = %s and d.type_id = %s' % (P.id, Q.id, C.id, E.id, D.id)
        self.assertEqual(0, rqs.count())
        self.assertEqual(getattr(rqs, '_cached_query').select, select)
        self.assertEqual(getattr(rqs, '_cached_query').count, count)
        self.assertEqual(0, len(rqs.filter())) # IGNORE:E1101
    
    def XXXtest_empty_chain_length_2_shorthand(self):
        """
        This shorthand notation is not yet supported by the compiler and maybe never will.
        """
        TMP = create(Namespace, 'tmp', 'http://tmp/tmp#')
        C, D, E = create((Concept, TMP, 'C'), (Concept, TMP, 'D'), (Concept, TMP, 'E'))
        one_one = Cardinality.objects.get(domain='1', range='1') # IGNORE:E1101
        P = create(Predicate, TMP, 'P', domain=C, range=D, cardinality=one_one)
        Q = create(Predicate, TMP, 'Q', domain=D, range=E, cardinality=one_one)
        rqs = SPARQLQuerySet().rdql(u'''
            select c.rdf:about, c.tmp:P.tmp:Q.rdf:about 
            from tmp:C c
            using tmp for "http://tmp/tmp#",
                  rdf for "http://www.w3.org/1999/02/22-rdf-syntax-ns#"''')
        select = u'''select c__tmp__P__o.name from rdf_resource c, rdf_statement c__tmp__P__s, rdf_resource c__tmp__P__o where c.type_id = %s and c__tmp__P__s.subject_id = c.id and c__tmp__P__s.predicate_id = %s and c__tmp__P__s.object_resource_id = c__tmp__P__o.id''' % (C.id, P.id)
        count = u'''select count(*) from rdf_resource c, rdf_statement c__tmp__P__s, rdf_resource c__tmp__P__o where c.type_id = %s and c__tmp__P__s.subject_id = c.id and c__tmp__P__s.predicate_id = %s and c__tmp__P__s.object_resource_id = c__tmp__P__o.id''' % (C.id, P.id)
        self.assertEqual(0, rqs.count())
        self.assertEqual(getattr(rqs, '_cached_query').select, select)
        self.assertEqual(getattr(rqs, '_cached_query').count, count)
        self.assertEqual(0, len(rqs.filter())) # IGNORE:E1101
    
    def test_empty_chain_length_5(self):
        DC = get(Namespace, 'dc')
        TMP = create(Namespace, 'tmp', 'http://tmp/tmp#')
        TMQ = create(Namespace, 'tmq', 'http://tmq/tmq#')
        C, D, E, F, G = create(
            (Concept, TMP, 'C'), (Concept, TMP, 'D'), (Concept, TMP, 'E'), 
            (Concept, TMQ, 'F'), (Concept, TMQ, 'G'))
        one_one = Cardinality.objects.get(domain='1', range='1') # IGNORE:E1101
        P = create(Predicate, TMP, 'P', domain=C, range=D, cardinality=one_one)
        Q = create(Predicate, TMP, 'Q', domain=D, range=E, cardinality=one_one)
        R = create(Predicate, TMQ, 'R', domain=E, range=F, cardinality=one_one)
        S = create(Predicate, TMQ, 'S', domain=F, range=G, cardinality=one_one)
        rqs = SPARQLQuerySet().rdql(u'''
            select c.rdf:about, e.dc:title, g.dc:description 
            from tmp:C c, tmp:D d, tmp:E e, tmq:F f, tmq:G g
            where c tmp:P d
              and d tmp:Q e 
              and e tmq:R f
              and f tmq:S g
            using tmp for "http://tmp/tmp#",
                  tmq for "http://tmq/tmq#",
                  dc for "http://purl.org/dc/elements/1.1/",
                  rdf for "http://www.w3.org/1999/02/22-rdf-syntax-ns#"''')
        select = u'select c.name, e__dc__title__o.value, g__dc__description__o.value from rdf_statement e__dc__title__s, rdf_statement e__tmq__R__s, rdf_resource e, rdf_resource d, rdf_resource g, rdf_resource f, rdf_statement c__tmp__P__s, rdf_statement f__tmq__S__s, rdf_resource c, rdf_statement g__dc__description__s, rdf_string g__dc__description__o, rdf_statement d__tmp__Q__s, rdf_string e__dc__title__o where c__tmp__P__s.subject_id = c.id and c__tmp__P__s.predicate_id = %s and c__tmp__P__s.object_resource_id = d.id and d__tmp__Q__s.subject_id = d.id and d__tmp__Q__s.predicate_id = %s and d__tmp__Q__s.object_resource_id = e.id and e__tmq__R__s.subject_id = e.id and e__tmq__R__s.predicate_id = %s and e__tmq__R__s.object_resource_id = f.id and f__tmq__S__s.subject_id = f.id and f__tmq__S__s.predicate_id = %s and f__tmq__S__s.object_resource_id = g.id and c.type_id = %s and e.type_id = %s and d.type_id = %s and g.type_id = %s and f.type_id = %s and e__dc__title__s.subject_id = e.id and e__dc__title__s.predicate_id = %s and e__dc__title__s.id = e__dc__title__o.statement_id and g__dc__description__s.subject_id = g.id and g__dc__description__s.predicate_id = %s and g__dc__description__s.id = g__dc__description__o.statement_id' % (P.id, Q.id, R.id, S.id, C.id, E.id, D.id, G.id, F.id, DC['title'].id, DC['description'].id)
        count = u'select count(*) from rdf_statement e__dc__title__s, rdf_statement e__tmq__R__s, rdf_resource e, rdf_resource d, rdf_resource g, rdf_resource f, rdf_statement c__tmp__P__s, rdf_statement f__tmq__S__s, rdf_resource c, rdf_statement g__dc__description__s, rdf_string g__dc__description__o, rdf_statement d__tmp__Q__s, rdf_string e__dc__title__o where c__tmp__P__s.subject_id = c.id and c__tmp__P__s.predicate_id = %s and c__tmp__P__s.object_resource_id = d.id and d__tmp__Q__s.subject_id = d.id and d__tmp__Q__s.predicate_id = %s and d__tmp__Q__s.object_resource_id = e.id and e__tmq__R__s.subject_id = e.id and e__tmq__R__s.predicate_id = %s and e__tmq__R__s.object_resource_id = f.id and f__tmq__S__s.subject_id = f.id and f__tmq__S__s.predicate_id = %s and f__tmq__S__s.object_resource_id = g.id and c.type_id = %s and e.type_id = %s and d.type_id = %s and g.type_id = %s and f.type_id = %s and e__dc__title__s.subject_id = e.id and e__dc__title__s.predicate_id = %s and e__dc__title__s.id = e__dc__title__o.statement_id and g__dc__description__s.subject_id = g.id and g__dc__description__s.predicate_id = %s and g__dc__description__s.id = g__dc__description__o.statement_id' % (P.id, Q.id, R.id, S.id, C.id, E.id, D.id, G.id, F.id, DC['title'].id, DC['description'].id)
        self.assertEqual(0, rqs.count())
        self.assertEqual(getattr(rqs, '_cached_query').select, select)
        self.assertEqual(getattr(rqs, '_cached_query').count, count)
        self.assertEqual(0, len(rqs.filter())) # IGNORE:E1101
    
    def test_offsets_and_limits(self):
        XS = get(Namespace, 'xs')
        TMP = create(Namespace, 'tmp', 'http://tmp/tmp#')
        TEXT = XS['string']
        C = create(Concept, TMP, 'C') 
        one_one = Cardinality.objects.get(domain='1', range='1') # IGNORE:E1101
        P = create(Predicate, TMP, 'P', domain=C, range=TEXT, cardinality=one_one)
        for i in range(0, 20):
            r = create(Resource, TMP, 'r%s' % i, type=C)
            create(Statement, r, P, 'r%s' % i)
        _ = Concept.objects.values_for_concept(concept=C)
        self.assertEqual(20, len(_))
        self.assertEqual(20, _.count())
        _ = Concept.objects.values_for_concept(concept=C)[:10]
        self.assertEqual(10, _.count())
        self.assertEqual(10, len(_))
        _ = Concept.objects.values_for_concept(concept=C)[7:10]
        self.assertEqual(3, _.count())
        self.assertEqual(3, len(_))


class TestRDFManager(TestCase):

    def test_concept(self):
        XS = get(Namespace, 'xs')
        TEXT = XS['string']
        TMP = create(Namespace, 'tmp', 'http://tmp.tmp.tmp/tmp/tmp/')
        T = create(Concept, TMP, 'T')
        one_one = Cardinality.objects.get(domain='1', range='1') # IGNORE:E1101
        P = create(Predicate, TMP, 'P', domain=T, range=TEXT, cardinality=one_one)
        r = create(Resource, TMP, 'r', T)
        create(Statement, r, P, 'something clever')
        s = get(Statement, r, P)
        self.assertEqual(s.object, u'something clever')
        result = Concept.objects.values_for_concept(concept=T)
        self.assertEqual(1, result.count())

    def test_one_predicate_with_TEXT_range(self):
        XS = get(Namespace, 'xs')
        TEXT = XS['string']
        TMP = create(Namespace, 'tmp', 'http://tmp.tmp.tmp/tmp/tmp/')
        T = create(Concept, TMP, 'T', 'rdf.models.Resource')
        one_one = Cardinality.objects.get(domain='1', range='1') # IGNORE:E1101
        P = create(Predicate, TMP, 'P', domain=T, range=TEXT, cardinality=one_one)
        r = create(Resource, TMP, 'r', T)
        create(Statement, r, P, 'something clever')
        s = get(Statement, r, P)
        self.assertEqual(s.object, u'something clever')
        values = Concept.objects.values_for_predicates(P, domain=T)
        self.assertEqual(1, values.count())
        r_ = values[0]
        self.assertEqual(r_[P], s.object)

    def test_one_predicate_with_resource_range(self):
        TMP = create(Namespace, 'tmp', 'http://tmp/tmp#')
        T = create(Concept, TMP, 'T', 'rdf.models.Resource')
        one_one = Cardinality.objects.get(domain='1', range='1') # IGNORE:E1101
        P = create(Predicate, TMP, 'P', domain=T, range=T, cardinality=one_one)
        r0, r1 = create(Resource, TMP, 'r0', T), create(Resource, TMP, 'r1', T)
        create(Statement, r0, P, r1)
        values = Concept.objects.values_for_predicates(P, domain=T)
        self.assertEqual(1, values.count())
        r0_ = values[0]
        self.assertEqual(r0_[P], r1.name)

        
class TestPermissions(TestCase):
    
    def test_create(self):
        TMP = create(Namespace, 'tmp', 'http://tmp/tmp#')
        T = create(Concept, TMP, 'T', 'rdf.models.Resource')
        one_one = Cardinality.objects.get(domain='1', range='1') # IGNORE:E1101
        P = create(Predicate, TMP, 'P', domain=T, range=T, cardinality=one_one)
        
        from rdf.permissions import _permission_code, _permission_name, CODES_AND_NAMES
        for code, name in CODES_AND_NAMES:
            for instance in TMP, T, P:
                ct = ContentType.objects.get(
                    app_label=instance._meta.app_label, # IGNORE:W0212
                    model=instance._meta.object_name.lower()) # IGNORE:W0212
                permission = Permission.objects.get(content_type=ct, codename=_permission_code(instance, code)) # IGNORE:E1101
                self.assertEqual(_permission_name(instance, name), permission.name)


class TestViews(TestCase):
    
    def setUp(self):
        super(TestViews, self).setUp()
        self.user, _ = User.objects.get_or_create(username='test')
        self.user.set_password('test')
        self.user.save()
        self.client = Client()
        self.client.login(username='test', password='test')
    
        
         
