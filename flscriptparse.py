# -----------------------------------------------------------------------------
# flscriptparse.py
#
# Simple parser for FacturaLUX SCripting Language (QSA).  
# -----------------------------------------------------------------------------

import sys
import flex
import ply.yacc as yacc

# Get the token map
tokens = flex.tokens
start = "source"

reserv=['nonassoc']
reserv+=list(flex.reserved)


precedence = (
    set(reserv),
    ('nonassoc', 'EQUALS', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL', 'PLUSEQUAL', 'MINUSEQUAL',
    'LSHIFTEQUAL','RSHIFTEQUAL', 'ANDEQUAL', 'XOREQUAL', 'OREQUAL'),
    ('left','LOR', 'LAND'),
    ('right', 'LNOT'),
    ('left', 'LT', 'LE', 'GT', 'GE', 'EQ', 'NE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('left', 'OR', 'AND', 'NOT', 'XOR', 'LSHIFT', 'RSHIFT'),

)

def p_source(p):
    '''
    source  : docstring
            | classdeclaration
            | funcdeclaration
            | statement_list
    '''
    p[0]=[p[1]]


def p_source2(p):
    '''
    source  : source docstring
            | source classdeclaration
            | source funcdeclaration
            | source statement_list
    '''
    p[0]=p[1]+[p[2]]


    

def p_classdeclarationsource1(p):
    '''
    classdeclarationsource  : vardeclaration
                            | funcdeclaration
    '''
    p[0]=[p[1]]

def p_classdeclarationsource2(p):
    '''
    classdeclarationsource  : classdeclarationsource vardeclaration
                            | classdeclarationsource funcdeclaration
    '''
    p[0]=p[1]+[p[2]]

def p_basicsource(p):
    '''
    basicsource     : docstring
                    | statement_list
    '''
    p[0]=p[1]

def p_vardeclaration_list1(p):
    '''
    vardeclaration_list : vardeclaration
    '''
    p[0] = [p[1]]
    
def p_vardeclaration_list2(p):
    '''
    vardeclaration_list : vardeclaration_list vardeclaration
    '''
    p[0] = p[1] + [p[2]]
    

def p_statement(p):
    '''
    statement   : instruction
                | vardeclaration
                | ifstatement
                | whilestatement
                | withstatement
                | forstatement
                | switch
                | trycatch
    '''
    p[0] = p[1]

def p_optstatement_list(p):
    '''
    optstatement_list   : statement_list
                        | empty
    
    '''

def p_statement_list(p):
    '''
    statement_list      : statement
    statement_list      : statement_list statement
    statement_list      : LBRACE statement_list RBRACE
    '''
    
    '''
    print " ** ",
    for t in p.slice[1:]:
        print "%s" % (t.value),
        
    print " ** "'''
        
    #p[0] = [p[1]]
    #p[0] = p[1] + [p[2]]
    


def aux_vardeclaration(name,type=None,value=None):
    return {
            "name" : name,
            "type" : type,
            "value" : value,
        }

def p_optvartype(p):
    '''
    optvartype  : COLON ID
                | empty
    '''
    if len(p.slice) == 1: p[0] = None
    if len(p.slice) >  2: p[0] = p[2]
    

def p_vardeclaration(v):
    '''
    vardeclaration  :  VAR vardecl SEMI
                    |  CONST vardecl SEMI
                    |  error
    '''
    v[0] = v[1]

def p_vardeclaration_1(v):
    '''
    vardecl  :  ID optvartype
    '''
    v[0] = aux_vardeclaration(name=v[1],type=v[2])
    
def p_vardeclaration_2(v):
    '''
    vardecl  :  ID optvartype EQUALS expression 
    '''
    v[0] = aux_vardeclaration(name=v[1],type=v[2],value=v[4])
    
    

def p_arglist(p):
    '''
    arglist : vardecl
            | arglist COMMA vardecl
            | 
    '''
    if len(p.slice) == 1: p[0] = []
    if len(p.slice) == 2: p[0] = [p[1]]
    if len(p.slice) == 4: p[0] = p[1] + [p[3]]
        
    
    
def p_funcdeclaration(p):
    '''
    funcdeclaration : FUNCTION ID LPAREN arglist RPAREN optvartype LBRACE basicsource RBRACE
    '''
    p[0] = "function %s (%s)" % (p[2],p[4])
    
def p_callarg(p):
    '''
    callarg     : expression
                | variable PLUSPLUS
                | PLUSPLUS variable 
                | variable MINUSMINUS
                | MINUSMINUS variable 
    '''
    
def p_callargs(p):
    '''
    callargs    : callarg
                | callargs COMMA callarg
                | empty
    '''
    if len(p.slice) == 1: p[0] = []
    if len(p.slice) == 2: p[0] = [p[1]]
    if len(p.slice) == 4: p[0] = p[1] + [p[3]]

def p_funccall(p):
    '''
    funccall    : ID LPAREN callargs RPAREN
                | funccall PERIOD funccall
    '''
    p[0]=[p[1],p[3]]


def p_exprval(p):
    '''
    exprval : constant
            | NEW funccall
            | NEW ID
            | funccall
            | variable
            | variable PERIOD funccall
            | error
    '''
    p[0] = p[1]

def p_mathoperator(p):
    '''
    mathoperator    : PLUS
                    | MINUS
                    | TIMES
                    | DIVIDE
    '''

def p_expression(p):
    '''
    expression  : exprval
                | expression mathoperator exprval
                | exprval mathoperator expression
                | LPAREN expression RPAREN
                | LNOT LPAREN expression RPAREN
                | LNOT exprval
                | error
                | LPAREN condition RPAREN
    '''
    if len(p.slice) < 4: p[0] = [p[1]]
    else:  p[0] = [p[1],p[2],p[3]]
    
    
def p_variable(p):
    '''
    variable    : ID 
                | funccall PERIOD ID 
                | variable PERIOD ID
                | variable LBRACKET constant RBRACKET
                | variable LBRACKET ID RBRACKET
    '''
    
def p_storeinstruction(p):
    '''
        storeinstruction    : variable EQUALS expression 
                            | variable PLUSPLUS
                            | PLUSPLUS variable 
                            | variable MINUSMINUS
                            | MINUSMINUS variable 
                            | variable PLUSEQUAL expression
                            | variable MINUSEQUAL expression
            
    '''

def p_instruction(p):
    '''
    instruction : storeinstruction SEMI
                | funccall SEMI
                | RETURN expression SEMI
                | RETURN SEMI
                | THROW expression SEMI
                | BREAK SEMI
                | CONTINUE SEMI
    '''
    if p.slice[1].type=="funccall":
        p[0]="Ejecucion de '%s'" % (p[1])
    elif p.slice[1].type=="RETURN":
        p[0]="Se Retorna el valor '%s'" % (p[2])
    elif p.slice[1].type=="ID":
        p[0]="Variable '%s' asignada al valor '%s'" % (p[1], p[3])

def p_optextends(p):
    '''
    optextends  : EXTENDS ID
                | empty
    '''
    if len(p.slice) == 1: p[0] = None
    if len(p.slice) == 3: p[0] = p[2]
   
    
    
def p_classdeclaration(p):
    '''
    classdeclaration   : CLASS ID optextends LBRACE classdeclarationsource RBRACE
    '''
    p[0] = "class " + p[2]
    if p[3]: p[0] = "class %s (%s)" % (p[2], p[3])
    


def p_docstring(p):
    '''
    docstring   : DOCSTRINGOPEN AT ID COMMENTCLOSE
                | DOCSTRINGOPEN AT ID ID COMMENTCLOSE
    '''
    var = None
    if p.slice[4].type == "ID":
        var = p[4]
    
    p[0]=(p[3],var)    


# constant:
def p_constant(p): 
    '''constant : ICONST
                | FCONST
                | CCONST
                | SCONST
                | LCONST
                | error
              
              '''
    p[0] = p[1]

def p_statement_block(p):
    '''
    statement_block : statement
                    | LBRACE statement_list RBRACE
    '''

def p_optelse(p):
    '''
    optelse : ELSE statement_block
            | empty
    '''
def p_cmp_symbol(p):
    '''
    cmp_symbol  : LT
                | LE
                | GT
                | GE
                | EQ
                | NE
    '''

def p_boolcmp_symbol(p):
    '''
    boolcmp_symbol  : LOR
                    | LAND
    '''

def p_condition(p):
    '''
    condition   : expression cmp_symbol expression
    condition   : expression 
    condition   : condition boolcmp_symbol condition
    '''

def p_ifstatement(p):
    '''
    ifstatement : IF LPAREN condition RPAREN statement_block optelse
                | IF LPAREN expression RPAREN statement_block optelse
                | error
    '''

def p_whilestatement(p):
    '''
    whilestatement  : WHILE LPAREN condition RPAREN statement_block 
                    | WHILE LPAREN expression RPAREN statement_block 
                    | error
                    
    '''

def p_withstatement(p):
    '''
    withstatement   : WITH LPAREN ID RPAREN statement_block 
                    | error
    '''

def p_forstatement(p):
    '''
    forstatement    : FOR LPAREN storeinstruction SEMI condition SEMI storeinstruction RPAREN statement_block 
    forstatement    : FOR LPAREN VAR vardecl SEMI condition SEMI storeinstruction RPAREN statement_block 
                    | FOR LPAREN SEMI condition SEMI storeinstruction RPAREN statement_block 
                    | error
    '''


def p_case_block(p):
    '''
    case_block  :  CASE constant COLON statement_list BREAK SEMI
    case_block  :  CASE constant COLON LBRACE statement_list BREAK SEMI RBRACE
    case_block  :  CASE ID COLON LBRACE statement_list BREAK SEMI RBRACE
    case_block  :  CASE ID COLON statement_list BREAK SEMI
    case_block  :  CASE ID COLON LBRACE BREAK SEMI RBRACE
    '''

def p_case_block_list(p):
    '''
    case_block_list  :  case_block  
    case_block_list  :  case_block_list case_block  
    case_block_list  :  CASE constant COLON case_block_list  
    case_block_list  :  CASE ID COLON case_block_list  
    case_block_list  :  case_block_list CASE constant COLON case_block_list  
    case_block_list  :  case_block_list CASE ID COLON case_block_list  
    case_block_list  :  empty
    case_block_list  :  case_block_list DEFAULT COLON LBRACE statement_list RBRACE
    case_block_list  :  case_block_list DEFAULT COLON statement_list
    '''

def p_switch(p):
    '''
    switch  : SWITCH LPAREN expression RPAREN LBRACE case_block_list RBRACE
    '''
    
def p_optid(p):
    '''
    optid   : ID
            | empty
    '''
    
def p_trycatch(p):
    '''
    trycatch    : TRY LBRACE statement_list RBRACE CATCH LPAREN optid RPAREN LBRACE statement_list RBRACE
    trycatch    : TRY LBRACE statement_list RBRACE CATCH LPAREN optid RPAREN LBRACE RBRACE
    '''


def p_empty(t):
    'empty : '
    pass


error_count = 0
last_error_token = None

def p_error(t):
    global error_count
    global last_error_token
    if t != last_error_token:
        error_count += 1
        if error_count>100 or t is None: 
            yacc.errok()
            return
        try:
            print_context(t)
        except:
            pass
    #while 1:
    #    if t is None:
    #        print "*** Se encontro EOF intentando resolver el error *** "
    #        break
    #    if t.type == 'RBRACE': break
    #    if t.type == 'SEMI': break
    #    t = yacc.token()             # Get the next token
        
    #if t is not None:
    #    yacc.errok()
    #else:
    yacc.errok()
    t = yacc.token() 
    yacc.restart()
    last_error_token = t
    return t
        
    
# Build the grammar


parser = yacc.yacc(method='LALR',debug=False, 
      optimize = 0, write_tables = 1, debugfile = '/tmp/yaccdebug.txt',outputdir='/tmp/')

#profile.run("yacc.yacc(method='LALR')")

global input_data

def print_context(token):
    global input_data
    if not token: return
    last_cr = input_data.rfind('\n',0,token.lexpos)
    next_cr = input_data.find('\n',token.lexpos)
    column = (token.lexpos - last_cr)
    column1 = (token.lexpos - last_cr)
    while column1 < 16:
        column1 = (token.lexpos - last_cr)
        last_cr = input_data.rfind('\n',0,last_cr-1)

    print input_data[last_cr:next_cr].replace("\t"," ")
    print (" " * (column-1)) + "^", column, "#ERROR#" , token
    
    




def parse(data):
    global input_data
    parser.error = 0
    input_data = data
    p = parser.parse(data)
    if parser.error: return None
    return p

prog = "$$$"
if len(sys.argv) == 2:                               
    data = open(sys.argv[1]).read()                  
    prog = parse(data)                      
    if not prog: raise SystemExit                    
else:


    line = ""
    while 1:
        try:
            line += raw_input("flscript> ")
        except EOFError:                
            break;
        line += "\n"                    

    prog = parse(line)     

try:
    for line in prog:
        print ">>>" , line
except:
    print "Error GRAVE de parseo"




