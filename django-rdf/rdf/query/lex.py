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
