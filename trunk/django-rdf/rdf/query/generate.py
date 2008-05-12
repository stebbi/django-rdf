from ast import Variable


def generate(ast):

    def _select():
        return u'select ' + u', '.join(
            [_column(p) for p in ast.predicates])
    
    def _count():
        return u'select count(*)'
    
    def _column(predicate):
        if hasattr(predicate, '_spanned'):
            predicate = predicate._spanned
        if hasattr(predicate, '_generalized'):
            predicate = predicate._generalized
        if predicate.binding.literal:
            column = u'%s.%s' % (predicate.variable.name, predicate.binding.db_column)
        else:
            raise Exception('not supported')
        return column
    
    def _tables():
        return u'from ' + u', '.join(
            [_table(v) for v in ast.variables])
        
    def _table(variable):
        return u'%s %s' \
            % (variable.concept.binding.Model._meta.db_table, variable.name) # IGNORE:W0212
    
    def _where():
        if 1 > len(ast.constraints):
            return u''
        constraints = []
        for c in ast.constraints:
            if hasattr(c, '_generalized'):
                constraints.extend(c._generalized) # IGNORE:W0212
            else:
                constraints.append(c)
        return u'where ' + u' and '.join(
            [_where_clause(c) for c in constraints])
        
    def _where_clause(constraint):
        operator = '='
        left = _where_clause_left(constraint)
        right = _where_clause_right(constraint)
        return u' '.join([unicode(i) for i in (left, operator, right)])

    def _where_clause_left(constraint):
        if isinstance(constraint.object, Variable) and \
            constraint.object.concept.binding.literal:
            column = 'id'
        else:
            column = constraint.predicate.binding.db_column
        return u'.'.join((constraint.subject.name, column))

    def _where_clause_right(constraint):
        if not isinstance(constraint.object, Variable):
            return constraint.object # Constant
        if constraint.object.concept.binding.literal:
            column = 'statement_id'
        else:
            column = constraint.object.concept.binding.pk_column            
        return u'.'.join((constraint.object.name, column))
    
    def _range():
        if hasattr(ast, 'limit'):
            range = u'limit %s' % ast.limit
            if hasattr(ast, 'offset') and not ast.offset is None:
                range += u' offset %s' % ast.offset
        else:
            range = u''
        return range
    
    select_clause = _select()
    count_clause = _count()
    table_clause = _tables()
    where_clause = _where()
    range_clause = _range()
    select = u'%s %s %s %s' % (select_clause, table_clause, where_clause, range_clause)
    count = u'%s %s %s %s' % (count_clause, table_clause, where_clause, range_clause)
    return select.strip(), count.strip(), ast    

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
