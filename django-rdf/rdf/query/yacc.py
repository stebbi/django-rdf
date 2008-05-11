from rdf.query import ast 
from rdf.query.lex import lex, tokens


def p_rdql(p):
    'rdql : select from where using range'
    p[0] = p.parser


def p_select(p):
    'select : SELECT variable_and_predicate predicates'
    p[0] = p.parser.predicates
    
def p_select_all(p):
    'select : SELECT ASTERISK'
    # Can't figure out the right semantics... SQL semantics, or mandatory preds?
    raise Exception('Not implemented')

def p_predicates(p):
    'predicates : COMMA variable_and_predicate predicates'
    p[0] = p.parser.predicates

def p_no_predicates(p):
    'predicates : '
    p[0] = p.parser.predicates


def p_from(p):
    'from : FROM concept concepts'
    p[0] = p.parser.variables

def p_concepts(p):
    'concepts : COMMA concept concepts'
    p[0] = p.parser.variables

def p_no_concepts(p):
    'concepts : '
    p[0] = p.parser.variables


def p_empty_where(p):
    'where : '
    p[0] = None

def p_where(p):
    'where : WHERE constraint constraints'
    p[0] = p.parser.constraints

def p_constraints(p):
    'constraints : AND constraint constraints'
    p[0] = p.parser.constraints

def p_no_constraint(p):
    'constraints :'
    p[0] = p.parser.constraints


def p_empty_using(p):
    'using : '
    p[0] = None

def p_using(p):
    'using : USING namespace namespaces'
    p[0] = p.parser.namespaces
    
    
def p_empty_range(p):
    'range : '
    p[0] = None
    
def p_limit_no_offset(p):
    'range : limit'
    p.parser.limit = p[1]
    p.parser.offset = None
    p[0] = None
    
def p_limit_offset(p):
    'range : limit offset'
    p.parser.limit = p[1]
    p.parser.offset = p[2]
    p[0] = None
    
def p_offset_limit(p):
    'range : offset limit'
    p.parser.offset = p[1]
    p.parser.limit = p[2]
    p[0] = None
    
def p_limit(p): 
    'limit : LIMIT INTEGER'
    p[0] = p[2]

def p_offset(p):
    'offset : OFFSET INTEGER'
    p[0] = p[2]


def p_variable_and_predicate(p):
    'variable_and_predicate : variable_name DOT predicate_name_or_code'
    p[3].variable = p.parser.variables[p[1]]
    p.parser.predicates.append(p[3])
    p[0] = p.parser.predicates
    
def p_predicate_without_variable(p):
    'variable_and_predicate : predicate_name_or_code'
    p[1].variable = p.parser.variables.DEFAULT
    p.parser.predicates.append(p[1])
    p[0] = p.parser.predicates
    
def p_predicate_name_or_code(p):
    'predicate_name_or_code : SYMBOL'
    name, namespace = p[1], None
    if -1 != name.find(':'):
        namespace_code, name = name.split(':')
        namespace = p.parser.namespaces[namespace_code]
    p[0] = ast.PredicateRef(
        name=name, namespace=namespace, position=(p.lineno(1), p.lexpos(1)))


def p_concept_as_name(p):
    'concept : concept_code_or_name AS variable_name'
    p_named_concept(p)

def p_named_concept(p):
    'concept : concept_code_or_name variable_name'
    v = p[2]
    v.concept = p[1]
    v.position = p[1].position
    p[0] = p.parser.variables

def p_unnamed_concept(p):
    'concept : concept_code_or_name'
    v = p.parser.variables[p[1].name]
    v.concept = p[1]
    v.position = p.lineno(1), p.lexpos(1)
    p[0] = v

def p_concept_code_or_name(p):
    'concept_code_or_name : SYMBOL'
    name, namespace = p[1], None
    if -1 != name.find(':'):
        namespace_code, name = name.split(':')
        namespace = p.parser.namespaces[namespace_code]
    p[0] = ast.ConceptRef(
        name=name, namespace=namespace, position=(p.lineno(1), p.lexpos(1)))


def p_variable_name_not_constant(p):
    'variable_name_or_constant : variable_name'
    p[0] = p[1]
    
def p_variable_name(p):
    'variable_name : SYMBOL'
    p[0] = p.parser.variables[p[1]] 

def p_constant_not_variable_name(p):
    'variable_name_or_constant : constant'
    p[0] = p[1]
    
def p_string_constant(p):
    'constant : STRING'
    p[0] = '"' + p[1] + '"'
    
def p_decimal_constant(p):
    'constant : DECIMAL'
    p[0] = p[1]

def p_integer_constant(p):
    'constant : INTEGER'
    p[0] = p[1]


def p_constraint(p):
    'constraint : variable_name predicate_name_or_code variable_name_or_constant'
    c = ast.Constraint(
        subject=p[1], predicate=p[2], object=p[3], 
        position=(p.lineno(1), p.lexpos(1)))
    p.parser.constraints.append(c)
    p[0] = c


def p_namespaces(p):
    'namespaces : COMMA namespace namespaces'
    p[0] = p.parser.namespaces

def p_no_namespace(p):
    'namespaces : '
    p[0] = p.parser.namespaces

def p_namespace_with_code(p):
    'namespace : namespace_code FOR namespace_uri'
    n = p[1]
    n.uri = p[3]
    p[0] = n
    
def p_namespace_code(p):
    'namespace_code : SYMBOL'
    n = p.parser.namespaces[p[1]]
    n.position = p.lineno(1), p.lexpos(1)
    p[0] = n
    
def p_namespace_uri(p):
    'namespace_uri : STRING'
    p[0] = p[1]

def p_namespace_without_code(p):
    'namespace : STRING'
    n = p.parser.namespaces.DEFAULT
    n.uri = p[1]
    n.position = p.lineno(1), p.lexpos(1)
    p[0] = n

def p_error(p):
    raise SyntaxError(unicode(p))


def Parser():
    from ply.yacc import yacc
    _ = yacc()
    _.namespaces = ast.Namespaces()
    _.variables = ast.Variables()
    _.predicates = ast.Predicates()
    _.constraints = ast.Constraints()
    return _

