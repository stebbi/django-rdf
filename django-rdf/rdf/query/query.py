from django.db import connection
from django.db.models.query import QuerySet, EmptyResultSet, GET_ITERATOR_CHUNK_SIZE

from rdf.query.compiler import Compiler


class SPARQLQuerySet(QuerySet):
        
    def __init__(self, *args, **kwargs):
        super(SPARQLQuerySet, self).__init__(*args, **kwargs) # IGNORE:W0142
        self._rdql = None
        self._cached_query = None
        self._mangle = False
        
    def rdql(self, rdql, mangle=False):
        self._rdql, self._mangle = rdql, mangle
        return self
    
    def count(self):
        return super(SPARQLQuerySet, self).count() \
            if self._rdql is None else \
            self._rdql_count()
            
    def iterator(self):
        return super(SPARQLQuerySet, self).iterator() \
            if self._rdql is None else \
            self._rdql_iterator()
            
    def _clone(self, cls=None, **kwargs):
        c = super(SPARQLQuerySet, self)._clone(cls, **kwargs) # IGNORE:W0142
        c._rdql = self._rdql
        c._mangle = self._mangle
        c._cached_query = self._cached_query
        return c
    
    def _get_sql_clause(self, clause='select'): # IGNORE:W0221
        if self._rdql is None:
            return super(SPARQLQuerySet, self)._get_sql_clause()
        if self._cached_query is None:
            q = Query(rdql=self._rdql)
            q.compile()
            self._cached_query = q
        sql = getattr(self._cached_query, clause) # IGNORE:E1101
        if 'select' == clause:
            sql = self.limit_offset_sql(sql)
        elif 'count' == clause:
            pass
        else:
            assert False, 'unrecognized type of SQL clause requested (`%s`)' % clause
        return sql
    
    def _rdql_count(self):
        try: 
            sql = self._get_sql_clause(clause='count') # IGNORE:E1101
        except EmptyResultSet:
            return 0            
        cursor = connection.cursor() # IGNORE:E1101
        cursor.execute(sql) # IGNORE:E1101
        count = cursor.fetchone()[0]
        cursor.close()
        if self._offset:
            count = max(0, count - self._offset)
        if self._limit:
            count = min(self._limit, count)
        return count

    def _rdql_iterator(self):
        try:
            sql = self._get_sql_clause()
        except EmptyResultSet:
            raise StopIteration
        cursor = connection.cursor() # IGNORE:E1101
        cursor.execute(sql) # IGNORE:E1101
        predicates = self._cached_query.mangled_predicates \
            if self._mangle else self._cached_query.predicates  
        while 1:
            rows = cursor.fetchmany(GET_ITERATOR_CHUNK_SIZE)
            if not rows:
                raise StopIteration
            for row in rows:
                yield dict(zip(predicates, row)) # IGNORE:E1101
        cursor.close()

    def limit_offset_sql(self, sql):
        if not self._limit is None:
            sql += ' %s' % connection.ops.limit_offset_sql(self._limit, self._offset)
        return sql

class Query(object):

    def __init__(self, **kwargs):
        self.rdql = kwargs['rdql']
        self.select, self.count = None, None
        self.predicates, self.mangled_predicates = None, None

    def compile(self):
        c = Compiler()
        self.select, self.count = c.compile(self.rdql)
        self.predicates = c.predicates
        self.mangled_predicates = c.mangled_predicates
        return self

