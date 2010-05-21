# -----------------------------------------------------------------------------
# flscriptparse.py
#
# Simple parser for FacturaLUX SCripting Language (QSA).  
# -----------------------------------------------------------------------------

import sys, math
import hashlib
import flex
import ply.yacc as yacc
import ply.lex as lex
        
from flclasses import *

# Get the token map
tokens = flex.tokens
start = "source"

reserv=['nonassoc']
reserv+=list(flex.reserved)

def cnvrt(val):
    return str(val).replace('"','\\"')

precedence = (
    ('nonassoc', 'EQUALS', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL', 'PLUSEQUAL', 'MINUSEQUAL'),
    ('left','LOR', 'LAND'),
    ('right', 'LNOT'),
    ('left', 'LT', 'LE', 'GT', 'GE', 'EQ', 'NE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('left', 'OR', 'AND', 'XOR', 'LSHIFT', 'RSHIFT'),

)

def p_parse(token):
    '''
    exprval : constant
            | variable
            | funccall
            | error

    base_expression     : exprval
                        | base_expression mathoperator base_expression
                        | base_expression cmp_symbol base_expression
                        | base_expression boolcmp_symbol base_expression
                        | LPAREN base_expression RPAREN
                        | LNOT base_expression
                        | MINUS base_expression
                        | PLUS base_expression
                        | NEW funccall_1
                        | NEW ID
                        | base_expression CONDITIONAL1 base_expression COLON base_expression

    expression  : base_expression
                | error

    case_cblock_list  :  case_block  
    case_cblock_list  :  case_cblock_list case_block  

    case_block  :  CASE base_expression COLON statement_list 

    id_or_constant  : variable
                    | constant

    case_default    :  DEFAULT COLON statement_list

    case_block_list  :  empty
    case_block_list  :  case_default
    case_block_list  :  case_cblock_list 
    case_block_list  :  case_cblock_list case_default

    source_element  : docstring
                    | vardeclaration
                    | classdeclaration
                    | funcdeclaration

    source  : source_element
    source  : source source_element
            | statement_list
    

    basicsource     : statement_list
                    | empty

    statement   : instruction
                | vardeclaration
                | ifstatement
                | whilestatement
                | withstatement
                | forstatement
                | switch
                | trycatch

    statement_list      : statement_list statement

    statement_list      : statement 

    statement_list      : LBRACE statement_list RBRACE

    statement_list      : LBRACE RBRACE
    statement_list      : empty

    optvartype  : COLON ID
                | empty

    vardeclaration  :  VAR vardecl_list SEMI
                    |  CONST vardecl_list SEMI
    vardeclaration  :  VAR vardecl_list 
                    |  CONST vardecl_list 

    vardecl  :  ID optvartype EQUALS expression 
    vardecl  :  ID optvartype

    vardecl_list    : vardecl
                    | vardecl_list COMMA vardecl

    arglist : vardecl_list
            |

    funcdeclaration : FUNCTION ID LPAREN arglist RPAREN optvartype LBRACE basicsource RBRACE

    callarg     : expression

    callargs    : callarg
                | callargs COMMA callarg
                | empty

    varmemcall  : variable_1
                | funccall_1
                | member_call
                | member_var
                | base_expression 

    member_var  : varmemcall PERIOD variable_1
    member_call : LPAREN member_var RPAREN PERIOD funccall_1

    member_call : varmemcall PERIOD funccall_1
    member_call : LPAREN member_call RPAREN PERIOD funccall_1

    funccall    : funccall_1
                | member_call
                | LPAREN member_call RPAREN
                | LPAREN funccall_1 RPAREN

    funccall_1  : ID LPAREN callargs RPAREN
                | ID LPAREN RPAREN

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

    variable    : variable_1
                | member_var
                | LPAREN variable_1 RPAREN 
                | LPAREN member_var RPAREN

    variable_1  : ID 
                | inlinestoreinstruction
                | variable_1 LBRACKET base_expression RBRACKET
                | funccall_1 LBRACKET base_expression RBRACKET

    inlinestoreinstruction  : PLUSPLUS ID 
                            | MINUSMINUS ID 
                            | ID PLUSPLUS 
                            | ID MINUSMINUS 

        storeequalinstruction   : variable EQUALS expression 
                                | variable EQUALS storeequalinstruction


        storeinstructionbasic   : storeequalinstruction
                                | inlinestoreinstruction
            

        storeinstruction    : inlinestoreinstruction
                            | storeequalinstruction
                            | variable PLUSEQUAL expression
                            | variable MINUSEQUAL expression
                            | variable MODEQUAL expression
                            | variable DIVEQUAL expression
                            | variable TIMESEQUAL expression
                            | DELETE variable
            

    flowinstruction : RETURN expression 
                    | THROW expression 
                    | RETURN 
                    | BREAK 
                    | CONTINUE 

    instruction : base_instruction SEMI
                | SEMI
                | base_instruction 
    base_instruction : storeinstruction
                | funccall 
                | flowinstruction 
                | variable
                | variable PLUSPLUS
                | variable MINUSMINUS

    optextends  : EXTENDS ID
                | empty

    classdeclaration   : CLASS ID optextends LBRACE classdeclarationsource RBRACE

    classdeclarationsource  : vardeclaration
                            | funcdeclaration
                            | classdeclarationsource vardeclaration
                            | classdeclarationsource funcdeclaration
                            | SEMI
                            | classdeclarationsource SEMI

    docstring   : DOCSTRINGOPEN AT ID COMMENTCLOSE
                | DOCSTRINGOPEN AT ID ID COMMENTCLOSE

    list_constant   : LBRACKET callargs RBRACKET
    list_constant   : LBRACKET callargs COMMA RBRACKET

    constant : ICONST
                | FCONST
                | CCONST
                | SCONST
                | RXCONST
                | list_constant
                | error
              

    statement_block : statement
                    | LBRACE statement_list RBRACE

    optelse : ELSE statement_block
            | empty

    cmp_symbol  : LT
                | LE
                | GT
                | GE
                | EQ
                | NE

    boolcmp_symbol  : LOR
                    | LAND

    condition   : expression 

    ifstatement : IF LPAREN condition RPAREN statement_block optelse

    whilestatement  : WHILE LPAREN condition RPAREN statement_block 
    whilestatement  : DO statement_block WHILE LPAREN condition RPAREN SEMI
                    | error

    withstatement   : WITH LPAREN variable RPAREN statement_block 
                    | error

    forstatement    : FOR LPAREN storeinstruction SEMI base_expression SEMI storeinstruction RPAREN statement_block 
    forstatement    : FOR LPAREN VAR vardecl SEMI base_expression SEMI storeinstruction RPAREN statement_block 
                    | FOR LPAREN SEMI base_expression SEMI storeinstruction RPAREN statement_block 
                    | error

    switch  : SWITCH LPAREN expression RPAREN LBRACE case_block_list RBRACE

    optid   : ID
            | empty

    trycatch    : TRY LBRACE statement_list RBRACE CATCH LPAREN optid RPAREN LBRACE statement_list RBRACE
    trycatch    : TRY LBRACE statement_list RBRACE CATCH LPAREN optid RPAREN LBRACE RBRACE

    empty : 
    '''
    lexspan = list(token.lexspan(0))
    data = str(token.lexer.lexdata[lexspan[0]:lexspan[1]])
    token[0] = { "02-size" : lexspan,  "50-contents" :  [ { "01-type": s.type, "99-value" : s.value} for s in token.slice[1:] ] } 


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
        print "ERROR"
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


parser = yacc.yacc(method='LALR',debug=0, 
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
    
    
def my_tokenfunc(*args, **kwargs):
    #print "Call token:" ,args, kwargs
    ret = lex.lexer.token(*args, **kwargs)    
    #print "Return (",args, kwargs,") = " , ret
    return ret


def print_tokentree(token, depth = 0):
    print "  " * depth, token.__class__ , "=" , token
    
    if str(token.__class__) == "ply.yacc.YaccProduction":
        print token.lexer
        for tk in token.slice:    
            if tk.value == token: continue
            print "  " * (depth+1), tk.type, 
            try:
                print tk.lexpos, 
                print tk.endlexpos,
            except:
                pass
            print 
            
            print_tokentree(tk.value, depth +1)

def calctree(obj, depth = 0, num = [], otype = "source"):
    #if depth > 5: return
    source_data = [
        'source',
        'source_element',
        'statement_list',
        'statement',
        'classdeclarationsource',
        'vardecl_list',
    ]
    final_obj = {}
    final_obj['range'] = obj['02-size'] 
    has_data = 0
    has_objects = 0
    contentlist = []
    ctype_alias = {
        "member_var" : "member",
        "member_call" : "member",
        "variable_1" : "variable",
        "funccall_1" : "funccall",
        "flowinstruction" : "instruction",
        "storeequalinstruction" : "instruction",
        "vardecl" : "vardeclaration",
        #"vardecl_list" : "vardeclaration",
        
    }
    if otype in ctype_alias:
        otype = ctype_alias[otype]
    #print " " * depth , obj['02-size']
    for n,content in enumerate(obj['50-contents']):
        ctype = content['01-type']
        value = content['99-value']
        if ctype in ctype_alias:
            ctype = ctype_alias[ctype]
        #if ctype in source_data:
        #    if depth == 0: print "--"
        #    print_tree(value,depth,num)
        #    continue
        #print " " * depth , "%s:" % ".".join(num+[str(n)]), ctype,
        
        if type(value) is dict:
            #print "*"
            tree_obj = calctree(value,depth+1,num+[str(n)], ctype)
            if type(tree_obj) is dict:
                if tree_obj['has_data'] and ctype != otype:
                    contentlist.append([ctype,tree_obj])
                    has_objects += 1
                else:
                    contentlist+=tree_obj["content"]
                    has_data += tree_obj["has_data"]
                    has_objects += tree_obj["has_objects"]
        else:
            #print "=", repr(value)
            contentlist.append([ctype,value])
            has_data += 1

    final_obj['content'] = contentlist
    final_obj['has_data'] = has_data
    final_obj['has_objects'] = has_objects
    
    return final_obj
    

hashes = []

def printtree(tree, depth = 0, otype = "source"):
    global hashes
    sep = "    "
    marginblocks = {
        "classdeclaration" : 3,
        "funcdeclaration" : 2,
        "statement_block" : 3,
        "instruction" : 1,
    }
    closingtokens = [
        "RBRACE",
        "RPAREN",
        "RBRACKET",
        "SEMI",
    ]
    nuevalinea = False
    name = ""
    lines = []
    
        
    
    for ctype, value in tree['content']:
        if nuevalinea and ctype in closingtokens:
            nuevalinea = False
        
        if nuevalinea: 
            for i in range(int(math.ceil(l/2.0))): lines.append(sep * depth)
            nuevalinea = False
            
        if type(value) is dict and ctype == otype:
            tname,tlines,trange = printtree(value, depth, ctype)
            lines += tlines
        elif type(value) is dict:
            l = 0
            if ctype in marginblocks: l = marginblocks[ctype]
                
            for i in range(int(math.floor(l/2.0))): lines.append(sep * depth)
            tname,tlines,trange = printtree(value, depth+1, ctype)
            # lines.append(sep * depth + "<!-- %d -->" % (len("".join(tlines))))
            
            if value['has_data'] > 0 and value['has_objects'] == 0:
                # Do it inline!
                if value['has_data']==1 and tname:
                    lines.append(sep * depth + "<%s id=\"%s\" />" % (ctype,tname))
                else:
                    txt = "".join([ x.strip() for x in tlines])
                    lines.append(sep * depth + "<%s>%s</%s>" % (ctype,txt,ctype))
            else:
                attrs = []
                if tname:
                    attrs.append(("id",tname))
                
                txtinline = "".join([ line.strip() for line in tlines ])
                    
                #if len(tlines)>1:
                txthash = hashlib.sha1(txtinline).hexdigest()[:16]
                #hashes.append(("depth:",depth,"hash:",txthash,"element:",ctype+":"+tname)) 
                hashes.append((txthash,ctype+":"+tname+"(%d)"% len(txtinline))) 
                #,"start:",trange[0],"end:",trange[1]))
                #attrs.append(("start",trange[0]))
                #attrs.append(("end",trange[1]))
                #attrs.append(("hash",txthash))
                    
                txtattrs=""
                for name1, val1 in attrs:
                    txtattrs+=" %s=\"%s\"" % (name1,cnvrt(val1))
                    
                lines.append(sep * depth + "<%s%s>" % (ctype,txtattrs))
                if depth > 50:
                    lines.append(sep * (depth+1) + "...")
                else:
                    if len(txtinline)<80:
                        lines.append(sep * (depth+1) + txtinline)
                    else:
                        lines+=tlines
                if txtattrs:
                    txtattrs = "<!--%s -->" % txtattrs
                lines.append(sep * depth + "</%s> %s" % (ctype, txtattrs))
                    
                nuevalinea = True
        else:
            if ctype == "ID" and name == "":
                name = value
            if ctype in flex.token_literals:
                lines.append(sep * depth +   "<%s value=\"%s\" />" % (ctype,cnvrt(value)))
            else:
                lines.append(sep * depth +  "<%s />" % (ctype))
                
        
    if depth == 0:
        #print "\n".join(lines)
        for row in sorted(set(hashes)):
            row = list(row)
            row[0] = row[0][8:] + row[0][:8]
            print "  ".join(row)
            #print "  ".join([ str(x) for x in row])
    return name, lines, tree['range']
        


def parse(data):
    global input_data
    parser.error = 0
    input_data = data
    p = parser.parse(data, debug = 0, tracking = 1, tokenfunc = my_tokenfunc)
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

tree_data = calctree(prog)
printtree( tree_data)

"""
import yaml

print yaml.dump(tree_data)
"""
#print_tokentree(prog)

    


#for varName in prog.byDefName:
#    var = prog.byDefName[varName]
#    print "%-15s / %-15s > " % var.type  , varName
        

#import tests.ifaceclass 
#tests.ifaceclass.do_test(prog)






