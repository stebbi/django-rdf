from decimal import Decimal
from ply import lex


tokens = (
    'STRING',
    'INTEGER', 
    'DECIMAL',
    'DOT', 
    'COMMA',
    'ASTERISK', 
    'SELECT',
    'FROM',
    'AS', 
    'WHERE',
    'AND',
    'USING', 
    'FOR',
    'OFFSET', 
    'LIMIT', 
    'SYMBOL',
    )

reserved = {
    'SELECT': 'SELECT', 
    'FROM': 'FROM', 
    'AS': 'AS', 
    'WHERE': 'WHERE', 
    'AND': 'AND', 
    'USING': 'USING',
    'FOR': 'FOR',
    'OFFSET': 'OFFSET', 
    'LIMIT': 'LIMIT', 
}

def t_STRING(t):
    r'''['"][^'"]*['"]'''
    t.value = t.value[1:-1]
    return t

def t_INTEGER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_DECIMAL(t):
    r'''\d+(\.\d+)?'''
    t.value = Decimal(t)
    return t

t_DOT = r'\.'

t_COMMA = r','

t_ASTERISK = r'\*'

def t_SYMBOL(t): 
    r'[\w_][\w\d_:\-\/\?\&]*'
    t.type = reserved.get(t.value.upper(), 'SYMBOL')
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \t\r'

def t_error(t):
    raise SyntaxError(unicode(t))


def Lexer():
    return lex.lex()


