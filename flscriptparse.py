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
    ('nonassoc', 'EQUALS', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL', 'PLUSEQUAL', 'MINUSEQUAL'),
    ('left','LOR', 'LAND'),
    ('right', 'LNOT'),
    ('left', 'LT', 'LE', 'GT', 'GE', 'EQ', 'NE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('left', 'OR', 'AND', 'XOR', 'LSHIFT', 'RSHIFT'),

)

def p_case_cblock_list(p):
    '''
    case_cblock_list  :  case_block  
    case_cblock_list  :  case_block_list case_block  
    '''
    p[0] = p[1:]

def p_case_block(p):
    '''
    case_block  :  CASE id_or_constant COLON BREAK SEMI
    case_block  :  CASE id_or_constant COLON LBRACE BREAK SEMI RBRACE
    case_block  :  CASE id_or_constant COLON statement_list BREAK SEMI
    case_block  :  CASE id_or_constant COLON LBRACE statement_list BREAK SEMI RBRACE
    case_block  :  CASE id_or_constant COLON case_block
    '''
    p[0] = p[1:]

def p_id_or_constant(p):
    '''
    id_or_constant  : ID
                    | constant
    '''
    p[0] = p[1:]
    
    
def p_case_default(p):
    '''
    case_default    :  DEFAULT COLON LBRACE statement_list RBRACE
    case_default    :  DEFAULT COLON statement_list
    case_default    :  empty
    '''
    p[0] = p[1:]

def p_case_block_list(p):
    '''
    case_block_list  :  empty
    case_block_list  :  case_default
    case_block_list  :  case_cblock_list case_default
    '''
    p[0] = p[1:]
    

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
    source  : source source 
    '''
    p[0]=p[1]+p[2]


    

def p_classdeclarationsource1(p):
    '''
    classdeclarationsource  : vardeclaration
                            | funcdeclaration
    '''
    if p[1]:
        p[0]=[p[1]]

def p_classdeclarationsource2(p):
    '''
    classdeclarationsource  : classdeclarationsource classdeclarationsource 
    '''
    try:
        p[0]=p[1]+p[2]
    except:
        p[0]=str(p[1])+str(p[2])

def p_basicsource(p):
    '''
    basicsource     : statement_list
                    | empty
    '''
    p[0]=p[1]
    

   

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


def p_statement_list1(p):
    '''
    statement_list      : statement_list statement
    '''
    p[0]=p[1]+[p[2]]

def p_statement_list2(p):
    '''
    statement_list      : statement 
    '''
    p[0]=[p[1]]

def p_statement_list3(p):
    '''
    statement_list      : LBRACE statement_list RBRACE
    '''
    p[0]=[p[2]]
    
    


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
    vardeclaration  :  VAR vardecl_list SEMI
                    |  CONST vardecl_list SEMI
    '''
    v[0] = (v[1],v[2])

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
    
    

def p_vardecl_list(p):
    '''
    vardecl_list    : vardecl
                    | vardecl_list COMMA vardecl
    '''
    if len(p.slice) == 1: p[0] = []
    if len(p.slice) == 2: p[0] = [p[1]]
    if len(p.slice) == 4: p[0] = p[1] + [p[3]]
        
def p_arglist(p):
    '''
    arglist : vardecl_list
            |
    '''
    if len(p.slice) == 1: p[0] = []
    else:  p[0] = p[1]
    
    
def p_funcdeclaration(p):
    '''
    funcdeclaration : FUNCTION ID LPAREN arglist RPAREN optvartype LBRACE basicsource RBRACE
    '''
    p[0] = "function %s (%s) : %s " % (p[2],p[4],p[6])
    if p[8]:
        p[0] += "{\n"
        for ln in p[8]:
            p[0] += str(ln) + "\n"
        p[0] += "\n}"
        
    else: p[0] += "{}"
    
    
def p_callarg(p):
    '''
    callarg     : expression
    '''
    p[0] = p[1:]
    
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
                | variable PERIOD funccall
                | funccall PERIOD funccall
                | LPAREN funccall RPAREN
    '''
    p[0] = []
    i=0
    for sl in p.slice:
        if i: p[0].append(sl.value)
        i+=1
    

def p_exprval(p):
    '''
    exprval : constant
            | funccall
            | variable
            | error
    '''
    p[0] = p[1]

def p_mathoperator(p):
    '''
    mathoperator    : PLUS
                    | MINUS
                    | TIMES
                    | DIVIDE
                    | MOD
                    | XOR
                    | OR
                    | LSHIFT
                    | RSHIFT
                    | AND
    '''
    p[0] = p[1:]

def p_expression(p):
    '''
    expression  : exprval
                | NEW funccall
                | NEW ID
                | expression mathoperator exprval
                | exprval mathoperator expression
                | LPAREN expression RPAREN
                | LNOT LPAREN expression RPAREN
                | LNOT exprval
                | error
                | LPAREN condition RPAREN
                | inlinestoreinstruction
                | expression boolcmp_symbol expression
                | expression cmp_symbol expression
    '''
    p[0] = p[1:]
    
    
def p_variable(p):
    '''
    variable    : ID 
                | funccall PERIOD variable 
                | variable PERIOD variable 
                | variable LBRACKET id_or_constant RBRACKET
                | variable LBRACKET exprval RBRACKET
                | variable LBRACKET inlinestoreinstruction RBRACKET
                | LPAREN variable RPAREN 
    '''
    p[0] = p[1:]

def p_inlinestoreinstruction(p):
    '''
    inlinestoreinstruction  : variable PLUSPLUS
                            | PLUSPLUS variable 
                            | variable MINUSMINUS
                            | MINUSMINUS variable 
    '''
    p[0] = p[1:]
    
def p_storeinstruction(p):
    '''
        storeinstruction    : variable EQUALS expression 
                            | inlinestoreinstruction
                            | variable PLUSEQUAL expression
                            | variable MINUSEQUAL expression
                            | variable MODEQUAL expression
                            | variable DIVEQUAL expression
                            | variable TIMESEQUAL expression
            
    '''
    p[0] = p[1:]

def p_instruction(p):
    '''
    instruction : storeinstruction SEMI
                | funccall SEMI
                | RETURN expression SEMI
                | RETURN SEMI
                | THROW expression SEMI
                | BREAK SEMI
                | CONTINUE SEMI
                | DELETE ID SEMI
                | SEMI
    '''
    p[0]=p[1:]
    """
    if p.slice[1].type=="funccall":
        p[0]="Ejecucion de '%s'" % (p[1])
    elif p.slice[1].type=="RETURN":
        p[0]="Se Retorna el valor '%s'" % (p[2])
    elif p.slice[1].type=="ID":
        p[0]="Variable '%s' asignada al valor '%s'" % (p[1], p[3])
        """

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
    if p[3]: p[0] = "class %s (extends %s)" % (p[2], p[3])

    if len(p[5]): 
        p[0] += "{\n"
        for ln in p[5]:
            p[0] += str(ln) + "\n"
        p[0] += "\n}"
        
    else: p[0] += "{}"
    


def p_docstring(p):
    '''
    docstring   : DOCSTRINGOPEN AT ID COMMENTCLOSE
                | DOCSTRINGOPEN AT ID ID COMMENTCLOSE
    '''
    var = None
    if p.slice[4].type == "ID":
        var = p[4]
    
    p[0]=(p[3],var)    

def p_list_constant(p):
    '''
    list_constant   : LBRACKET callargs RBRACKET
    '''
    p[0] = p[1:]
    
# constant:
def p_constant(p): 
    '''constant : ICONST
                | FCONST
                | CCONST
                | SCONST
                | list_constant
                | MINUS ICONST
                | MINUS FCONST
                | error
              
              '''
    p[0] = p[1]

def p_statement_block(p):
    '''
    statement_block : statement
                    | LBRACE statement_list RBRACE
    '''
    p[0] = p[1:]

def p_optelse(p):
    '''
    optelse : ELSE statement_block
            | empty
    '''
    p[0] = p[1:]

def p_cmp_symbol(p):
    '''
    cmp_symbol  : LT
                | LE
                | GT
                | GE
                | EQ
                | NE
    '''
    p[0] = p[1:]

def p_boolcmp_symbol(p):
    '''
    boolcmp_symbol  : LOR
                    | LAND
    '''
    p[0] = p[1:]

def p_condition(p):
    '''
    condition   : expression 
    '''
    p[0] = p[1:]

def p_ifstatement(p):
    '''
    ifstatement : IF LPAREN condition RPAREN statement_block optelse
                | error
    '''
    p[0] = p[1:]

def p_whilestatement(p):
    '''
    whilestatement  : WHILE LPAREN condition RPAREN statement_block 
    whilestatement  : DO statement_block WHILE LPAREN condition RPAREN SEMI
                    | error
                    
    '''
    p[0] = p[1:]

def p_withstatement(p):
    '''
    withstatement   : WITH LPAREN ID RPAREN statement_block 
                    | error
    '''
    p[0] = p[1:]

def p_forstatement(p):
    '''
    forstatement    : FOR LPAREN storeinstruction SEMI condition SEMI storeinstruction RPAREN statement_block 
    forstatement    : FOR LPAREN VAR vardecl SEMI condition SEMI storeinstruction RPAREN statement_block 
                    | FOR LPAREN SEMI condition SEMI storeinstruction RPAREN statement_block 
                    | error
    '''
    p[0] = p[1:]



def p_switch(p):
    '''
    switch  : SWITCH LPAREN expression RPAREN LBRACE case_block_list RBRACE
    '''
    p[0] = p[1:]
    
def p_optid(p):
    '''
    optid   : ID
            | empty
    '''
    p[0] = p[1:]
    
def p_trycatch(p):
    '''
    trycatch    : TRY LBRACE statement_list RBRACE CATCH LPAREN optid RPAREN LBRACE statement_list RBRACE
    trycatch    : TRY LBRACE statement_list RBRACE CATCH LPAREN optid RPAREN LBRACE RBRACE
    '''
    p[0] = p[1:]


def p_empty(t):
    'empty : '
    t[0] = []


error_count = 0
last_error_token = None

def p_error(t):
    global error_count
    global last_error_token
        

    if repr(t) != repr(last_error_token):
        error_count += 1
        if error_count>100 or t is None:         
            yacc.errok()
            return
        try:
            print_context(t)
        except:
            pass
        import sys
        sys.exit()
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
    if t is None:
        yacc.errok()
        return
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
    print
    
    




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




