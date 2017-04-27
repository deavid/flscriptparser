from __future__ import print_function
# ----------------------------------------------------------------------
# clex.py
#
# A lexer for ANSI C.
# ----------------------------------------------------------------------

#import sys
#sys.path.insert(0,"../..")

import ply.lex as lex
from ply.lex import TOKEN


# Reserved words
reserved = [
    'BREAK', 'CASE', 'CONST', 'STATIC', 'CONTINUE', 'DEFAULT', 'DO',
    'ELSE', 'FOR', 'IF', 'IN',
    'RETURN',
    #'STRUCT',
    'SWITCH',
    'WHILE', 'CLASS', 'VAR', 'FUNCTION',
    'EXTENDS', 'NEW','WITH','TRY','CATCH','THROW', 'DELETE', 'TYPEOF'
    ]
token_literals = [
    # Literals (identifier, integer constant, float constant, string constant, char const)
    'ID', 'ICONST', 'FCONST', 'SCONST', 'CCONST' #, 'RXCONST'
]
tokens = reserved + token_literals + [

    # Operators (+,-,*,/,%,|,&,~,^,<<,>>, ||, &&, !, <, <=, >, >=, ==, !=)
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'OR', 'AND',
    'CONDITIONAL1','AT',
    #'NOT',
    'XOR', 'LSHIFT', 'RSHIFT',
    'LOR', 'LAND', 'LNOT',
    'LT', 'LE', 'GT', 'GE', 'EQ', 'NE', 'EQQ', 'NEQ',

    # Assignment (=, *=, /=, %=, +=, -=, <<=, >>=, &=, ^=, |=)
    'EQUALS', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL', 'PLUSEQUAL', 'MINUSEQUAL',
#    'LSHIFTEQUAL','RSHIFTEQUAL', 'ANDEQUAL', 'XOREQUAL', 'OREQUAL',

    # Increment/decrement (++,--)
    'PLUSPLUS', 'MINUSMINUS',

    # Structure dereference (->)
#    'ARROW',

    # Conditional operator (?)
#    'CONDOP',

    # Delimeters ( ) [ ] { } , . ; :
    'LPAREN', 'RPAREN',
    'LBRACKET', 'RBRACKET',
    'LBRACE', 'RBRACE',
    'COMMA', 'PERIOD', 'SEMI', 'COLON',

    # Ellipsis (...)
#    'ELLIPSIS',
    'DOCSTRINGOPEN',
 #   'COMMENTOPEN',
    'COMMENTCLOSE',
    'DOLLAR',
    'SQOUTE',
    'DQOUTE',
    'BACKSLASH',
    ]

# Completely ignored characters
t_ignore           = ' \r\t\x0c'

# Newlines
@TOKEN(r'\n+')
def t_NEWLINE(t):
    t.lexer.lineno += t.value.count("\n")

# Operators
t_BACKSLASH       = '\\\\'
t_DOLLAR             = r'\$'
t_SQOUTE             = '\''
t_DQOUTE             = '"'
t_PLUS             = r'\+'
t_MINUS            = r'-'
t_TIMES            = r'\*'
t_DIVIDE           = r'/'
t_MOD              = r'%'
t_OR               = r'\|'
t_AND              = r'&'
#t_NOT              = r'~'
t_XOR              = r'\^'
t_LSHIFT           = r'<<'
t_RSHIFT           = r'>>'
t_LOR              = r'\|\|'
t_LAND             = r'&&'
t_LNOT             = r'!'
t_LT               = r'<'
t_GT               = r'>'
t_LE               = r'<='
t_GE               = r'>='
t_EQ               = r'=='
t_NE               = r'!='
t_EQQ               = r'==='
t_NEQ               = r'!=='
t_CONDITIONAL1      = r'\?'

# Assignment operators

t_EQUALS           = r'='
t_TIMESEQUAL       = r'\*='
t_DIVEQUAL         = r'/='
t_MODEQUAL         = r'%='
t_PLUSEQUAL        = r'\+='
t_MINUSEQUAL       = r'-='
"""
t_LSHIFTEQUAL      = r'<<='
t_RSHIFTEQUAL      = r'>>='
t_ANDEQUAL         = r'&='
t_OREQUAL          = r'\|='
t_XOREQUAL         = r'^='
"""

# Increment/decrement
t_PLUSPLUS         = r'\+\+'
t_MINUSMINUS       = r'--'

# ->
#t_ARROW            = r'->'

# ?
#t_CONDOP           = r'\?'


# Delimeters
t_LPAREN           = r'\('
t_RPAREN           = r'\)'
t_LBRACKET         = r'\['
t_RBRACKET         = r'\]'
t_LBRACE           = r'\{'
t_RBRACE           = r'\}'
t_COMMA            = r','
t_PERIOD           = r'\.'
t_SEMI             = r';'
t_COLON            = r':'
#t_ELLIPSIS         = r'\.\.\.'
t_AT               = r'@'
# Identifiers and reserved words

reserved_map = { }
for r in reserved:
    reserved_map[r.lower()] = r



@TOKEN(r'[A-Za-z_]+[\w_]*')
def t_ID(t):
    t.type = reserved_map.get(t.value,"ID")
    return t



# Integer literal
t_ICONST = r'\d+([uU]|[lL]|[uU][lL]|[lL][uU])?'

# Floating literal
t_FCONST = r'((\d+)(\.\d+)(e(\+|-)?(\d+))? | (\d+)e(\+|-)?(\d+))([lL]|[fF])?'

# String literal
t_SCONST = r'\"([^\"\\\n]|(\\.)|\\\n)*?\"'

# Character constant 'c' or L'c'
t_CCONST = r'\'([^\'\\\n]|(\\.)|\\\n)*?\''

# REGEX constant
#t_RXCONST = r'/[^/ ]+/g?'

# Comments
@TOKEN(r'(/\*( |\*\*)(.|\n)*?\*/)|(//.*)')
def t_comment(t):
    t.lexer.lineno += t.value.count('\n')


@TOKEN(r'/\*\*[ ]+')
def t_DOCSTRINGOPEN(t):
    return t;

#t_COMMENTOPEN      = r'/\*'
t_COMMENTCLOSE     = r'\*/'


# Preprocessor directive (ignored)
@TOKEN(r'\#(.)*?\n')
def t_preprocessor(t):
    t.lexer.lineno += 1


def t_error(t):
    print("Illegal character %s" % repr(t.value[0]))
    t.lexer.skip(1)


# TODO: Cada vez que se cambia este fichero, se tiene que lanzar sin el "-OO" de python para acelerar. Construye entonces
# ..... el fichero de cache que subimos a git, y se relee desde ahí las siguientes veces con el -OO.
# ..... Si da problemas, hay que volver a optimize=0 y/o eliminar lextab.py
lexer = lex.lex(debug=False,optimize=1)
if __name__ == "__main__":
    lex.runmain(lexer)





