from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from builtins import input
from builtins import str
from builtins import range
# -----------------------------------------------------------------------------
# flscriptparse.py
#
# Simple parser for FacturaLUX SCripting Language (QSA).
# -----------------------------------------------------------------------------
from optparse import OptionParser
import pprint
import sys, math
import hashlib
import ply.yacc as yacc
import ply.lex as lex

try:
    from pineboolib.flparser import flex
    from pineboolib.flparser.flclasses import *
except ImportError:
    import flex
    from flclasses import *

# Get the token map
tokens = flex.tokens
start = "source"

reserv=['nonassoc']
reserv+=list(flex.reserved)

endoffile = None

def cnvrt(val):
    val = str(val)
    val = val.replace('&','&amp;')
    val = val.replace('"','&quot;')
    val = val.replace("'",'&apos;')
    val = val.replace("<",'&lt;')
    val = val.replace(">",'&gt;')
    return val

precedence = (
    ('nonassoc', 'EQUALS', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL', 'PLUSEQUAL', 'MINUSEQUAL'),
    ('left','LOR', 'LAND'),
    ('left', 'LT', 'LE', 'GT', 'GE', 'EQ', 'NE', 'EQQ', 'NEQ'),
    ('right', 'LNOT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('left', 'OR', 'AND', 'XOR', 'LSHIFT', 'RSHIFT'),

)
seen_tokens = []
tokelines =  {}
last_lexspan = None

def p_parse(token):
    global input_data

    lexspan = list(token.lexspan(0))
    data = str(token.lexer.lexdata[lexspan[0]:lexspan[1]])
    if len(lexspan) == 2:
        fromline = token.lineno(0)
        global endoffile
        endoffile = fromline, lexspan, token.slice[0]
        #print fromline, lexspan, token.slice[0]
    token[0] = { "00-toktype": str(token.slice[0]), "02-size" : lexspan,  "50-contents" :  [ { "01-type": s.type, "99-value" : s.value} for s in token.slice[1:] ] }
    numelems = len([ s for s in token.slice[1:] if s.type != 'empty' and s.value is not None ])

    rspan = lexspan[0]
    if str(token.slice[0]) == 'empty' or numelems == 0: token[0] = None
    else:
        rvalues = []
        for n,s in enumerate(token.slice[1:]):
            if s.type != 'empty' and s.value is not None:
                val = None
                if isinstance(s.value,str):
                    val = token.lexspan(n+1)[0] + len(s.value) - 1
                else:
                    val = token.lexspan(n+1)[1]
                rvalues.append(val)
        rspan = max(rvalues)
    lexspan[1] = rspan

    #if str(token.slice[0]) == 'regexbody':
    #    token[0] = { "00-toktype": str(token.slice[0]) , "02-size" : lexspan,  "50-contents" :  input_data[lexspan[0]:lexspan[1]+1] }

    #if str(token.slice[0]) == 'regex':
    #    print "\r\n",str(token.slice[0]) ,":" , input_data[lexspan[0]:lexspan[1]+1]
    #    print "      " + "\n      ".join([ "%s(%r): %r" % (s.type, token.lexspan(n+1), s.value) for n,s in enumerate(token.slice[1:]) ])
    global seen_tokens, last_ok_token
    last_ok_token = token
    seen_tokens.append((str(token.slice[0]), token.lineno(0),input_data[lexspan[0]:lexspan[1]+1] ))
    global ok_count
    ok_count += 1
    if lexspan[0] not in tokelines:
        tokelines[lexspan[0]] = token.lexer.lineno
    global last_lexspan
    last_lexspan = lexspan
    
    



last_ok_token = None
error_count = 0
last_error_token = None
last_error_line = -1
ok_count = 0

def p_error(t):
    global error_count
    global ok_count
    global last_error_token
    global last_error_line, seen_tokens , last_ok_token
    debug = False # Poner a True para toneladas de debug.
    # if error_count == 0: print
    if t is not None:
        if last_error_token is None or t.lexpos != getattr(last_error_token,"lexpos",None):
            if abs(last_error_line -  t.lineno) > 4 and ok_count > 1 and error_count < 4:
                error_count += 1
                try: print_context(t)
                except Exception: pass
                if debug == True:
                    error_count += 20 # no imprimir mas de un error en debug.
                    print
                    for tokname, tokln, tokdata in seen_tokens[-32:]:
                        if tokln ==  t.lineno:
                            print(tokname, tokdata)
                    print(repr(last_ok_token[0]))
                    for s in last_ok_token.slice[:]:
                        print(">>>" ,  s.lineno, repr(s), pprint.pformat(s.value,depth=3))
                last_error_line = t.lineno
            elif abs(last_error_line -  t.lineno) > 1 and ok_count > 1:
                last_error_line = t.lineno
            parser.errok()
            ok_count = 0
            return

    ok_count = 0
    if t is None:
        if last_error_token != "EOF":
            print("ERROR: End of the file reached.")
            global endoffile
            print("Last data:", endoffile)

            if last_lexspan:
                try:
                    print("HINT: Last lexspan:", last_lexspan)
                    print("HINT: Last line:", tokelines[last_lexspan[0]])
                except Exception as e:
                    print("ERROR:", e)
        last_error_token = "EOF"
        return t
    t = parser.token()
    parser.restart()
    last_error_token = t
    return t

p_parse.__doc__ =     '''
    exprval : constant
            | variable
            | funccall
            | error

    identifier : ID

    dictobject_value : LBRACE RBRACE
                     | LBRACE dictobject_value_elemlist RBRACE

    dictobject_value_elemlist : dictobject_value_elem
                              | dictobject_value_elemlist COMMA dictobject_value_elem

    dictobject_value_elem : exprval COLON expression

    base_expression     : exprval
                        | inlinestoreinstruction
                        | base_expression mathoperator base_expression
                        | base_expression cmp_symbol base_expression
                        | base_expression boolcmp_symbol base_expression
                        | parentheses
                        | unary_operator
                        | new_operator
                        | ternary_operator
                        | dictobject_value
                        | typeof_operator




    parentheses         : LPAREN base_expression RPAREN
                        | LPAREN variable_1 RPAREN

    unary_operator      : LNOT base_expression
                        | MINUS base_expression
                        | PLUS base_expression

    new_operator        : NEW funccall_1
                        | NEW identifier

    typeof_operator     : TYPEOF variable
                        | TYPEOF base_expression

    ternary_operator    : base_expression CONDITIONAL1 base_expression COLON base_expression

    expression  : base_expression
                | funcdeclaration_anon
                | funcdeclaration_anon_exec
                | LPAREN expression RPAREN
                | error

    case_cblock_list  :  case_block
    case_cblock_list  :  case_cblock_list case_block

    case_block  :  CASE expression COLON statement_list

    case_default    :  DEFAULT COLON statement_list

    case_block_list  :  empty
    case_block_list  :  case_default
    case_block_list  :  case_cblock_list
    case_block_list  :  case_cblock_list case_default

    source_element  : docstring
                    | vardeclaration
                    | classdeclaration
                    | funcdeclaration
                    | funcdeclaration_anon
                    | funcdeclaration_anon_exec

    source  : source_element
    source  : source source_element
            | statement_list


    basicsource     : statement_list
                    | empty

    statement   : instruction
                | vardeclaration
                | ifstatement
                | whilestatement
                | dowhilestatement
                | withstatement
                | forstatement
                | forinstatement
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
                    |  STATIC VAR vardecl_list

    vardecl  :  ID optvartype EQUALS expression
    vardecl  :  ID optvartype

    vardecl_list    : vardecl
                    | vardecl_list COMMA vardecl

    arglist : vardecl_list
            |

    funcdeclaration : FUNCTION ID LPAREN arglist RPAREN optvartype LBRACE basicsource RBRACE
    funcdeclaration : STATIC FUNCTION ID LPAREN arglist RPAREN optvartype LBRACE basicsource RBRACE
    funcdeclaration_anon : FUNCTION LPAREN arglist RPAREN LBRACE basicsource RBRACE
                         | FUNCTION LPAREN RPAREN LBRACE basicsource RBRACE
    funcdeclaration_anon_exec : funcdeclaration_anon LPAREN RPAREN
                              | funcdeclaration_anon LPAREN arglist RPAREN

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
                | LPAREN error RPAREN

    funccall_1  : ID LPAREN callargs RPAREN
                | ID LPAREN RPAREN
                | TYPEOF LPAREN callargs RPAREN

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

    variable_1  : identifier
                | array_member

    array_member : variable_1 LBRACKET expression RBRACKET
                 | funccall_1 LBRACKET expression RBRACKET

    inlinestoreinstruction  : PLUSPLUS variable
                            | MINUSMINUS variable
                            | variable PLUSPLUS
                            | variable MINUSMINUS

        updateoperator : EQUALS
                       | PLUSEQUAL
                       | MINUSEQUAL
                       | MODEQUAL
                       | DIVEQUAL
                       | TIMESEQUAL

        updateinstruction : variable updateoperator expression
                          | variable updateoperator updateinstruction

        deleteinstruction   : DELETE variable

        storeinstruction    : inlinestoreinstruction
                            | updateinstruction
                            | deleteinstruction


    flowinstruction : RETURN expression
                    | THROW expression
                    | RETURN
                    | BREAK
                    | CONTINUE

    instruction : base_instruction SEMI
                | SEMI
                | base_instruction
                | funcdeclaration
                | error SEMI

    callinstruction : funccall
                    | variable

    base_instruction : storeinstruction
                | callinstruction
                | flowinstruction

    varorcall : variable
              | funccall
              | base_expression

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
                | regex
                | list_constant

    regex : DIVIDE regexbody DIVIDE regexflags
          | DIVIDE regexbody COMMENTCLOSE regexflags

    regexbody   : regexchar
                | regexbody regexchar

    regexchar :  LPAREN
              | RPAREN
              | ID
              | COMMA
              | XOR
              | LBRACKET
              | RBRACKET
              | ICONST
              | PLUS
              | MINUS
              | LBRACE
              | RBRACE
              | DOLLAR
              | SQOUTE
              | DQOUTE
              | PERIOD
              | BACKSLASH
              | CONDITIONAL1
              | EQUALS
              | OR
              | SCONST
	      | SEMI
              | error

    regexflags : ID
               | empty


    statement_block : statement
                    | LBRACE statement_list RBRACE
                    | LBRACE RBRACE

    optelse : ELSE statement_block
            | empty

    cmp_symbol  : LT
                | LE
                | GT
                | GE
                | EQ
                | NE
                | EQQ
                | NEQ
                | IN

    boolcmp_symbol  : LOR
                    | LAND

    condition   : expression
                | error

    ifstatement : IF LPAREN condition RPAREN statement_block optelse

    whilestatement  : WHILE LPAREN condition RPAREN statement_block
    dowhilestatement  : DO statement_block WHILE LPAREN condition RPAREN SEMI

    withstatement   : WITH LPAREN variable RPAREN statement_block
                    | error

    storeormember   : storeinstruction
                    | member_var

    for_initialize  : storeinstruction
                    | VAR vardecl
                    | for_initialize COMMA for_initialize
                    | empty

    for_compare     : expression
                    | empty

    for_increment   : storeormember
                    | for_increment COMMA for_increment
                    | empty


    forstatement    : FOR LPAREN for_initialize SEMI for_compare SEMI for_increment RPAREN statement_block
                    | error

    forinstatement  : FOR LPAREN for_initialize IN varorcall RPAREN statement_block
                    | FOR LPAREN variable IN varorcall RPAREN statement_block
                    | error

    switch  : SWITCH LPAREN condition RPAREN LBRACE case_block_list RBRACE

    optid   : ID
            | empty

    trycatch    : TRY statement_block CATCH LPAREN optid RPAREN statement_block

    empty :
    '''



# Build the grammar


parser = yacc.yacc(method='LALR',debug=0,
      optimize = 1, write_tables = 1, debugfile = '/tmp/yaccdebug.txt',outputdir='/tmp/')

#profile.run("yacc.yacc(method='LALR')")

global input_data

def print_context(token):
    global input_data
    if token is None: return
    last_cr = input_data.rfind('\n',0,token.lexpos)
    next_cr = input_data.find('\n',token.lexpos)
    column = (token.lexpos - last_cr)
    column1 = (token.lexpos - last_cr)
    while column1 < 16:
        column1 = (token.lexpos - last_cr)
        last_cr = input_data.rfind('\n',0,last_cr-1)

    print(input_data[last_cr:next_cr].replace("\t"," "))
    print((" " * (column-1)) + "^", column, "#ERROR#" , token)


def my_tokenfunc(*args, **kwargs):
    #print("Call token:" ,args, kwargs)
    ret = lex.lexer.token(*args, **kwargs)
    #print "Return (",args, kwargs,") = " , ret
    return ret


def print_tokentree(token, depth = 0):
    print("  " * depth, token.__class__ , "=" , token)

    if str(token.__class__) == "ply.yacc.YaccProduction":
        print(token.lexer)
        for tk in token.slice:
            if tk.value == token: continue
            print("  " * (depth+1), tk.type, end=' ')
            try:
                print(tk.lexpos, end=' ')
                print(tk.endlexpos, end=' ')
            except:
                pass
            print()

            print_tokentree(tk.value, depth +1)

def calctree(obj, depth = 0, num = [], otype = "source", alias_mode = 1):
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

    if alias_mode == 0:
        ctype_alias = {}
    elif alias_mode == 1:
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
    else:
        raise ValueError("alias_mode unknown")

    if otype in ctype_alias:
        otype = ctype_alias[otype]
    #print " " * depth , obj['02-size']
    for n,content in enumerate(obj['50-contents']):
        if not isinstance(content,dict):
            print("ERROR: content is not a dict!:", repr(content))
            print(".. obj:", repr(obj))
            raise TypeError("content is not a dict")
            continue
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
            if depth < 600:
                try:
                    tree_obj = calctree(value,depth+1,num+[str(n)], ctype, alias_mode=alias_mode)
                except Exception:
                    print("ERROR: trying to calculate member %d on:" % n, repr(obj))
            else:
                tree_obj = None
            if type(tree_obj) is dict:
                if (tree_obj['has_data'] or alias_mode == 0) and ctype != otype :
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
ranges = []
def printtree(tree, depth = 0, otype = "source", mode = None, output = sys.stdout):
    global hashes, ranges
    if depth == 0:
        hashes = []
        ranges = []

    sep = "    "
    marginblocks = {
        "classdeclaration" : 1,
        "funcdeclaration" : 1,
        "statement_block" : 1,
        #"instruction" : 1,
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
    l = 0


    for ctype, value in tree['content']:
        if nuevalinea and ctype in closingtokens:
            nuevalinea = False

        if nuevalinea:
            for i in range(int(math.ceil(l/2.0))):
                lines.append(sep * depth)
            nuevalinea = False

        if type(value) is dict and ctype == otype:
            tname,tlines,trange = printtree(value, depth, ctype)
            if name == "" and tname:
                name = tname

            lines += tlines
        elif type(value) is dict:
            l = 0
            if ctype in marginblocks: l = marginblocks[ctype]

            for i in range(int(math.floor(l/2.0))):
                lines.append(sep * depth)
            tname,tlines,trange = printtree(value, depth+1, ctype)
            # lines.append(sep * depth + "<!-- %d -->" % (len("".join(tlines))))

            if value['has_data'] > 0 and value['has_objects'] == 0 and False:
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
                ranges.append([depth,txthash]+trange+[ctype+":"+tname,len(txtinline)])
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
                lines.append(sep * depth + "</%s>" % (ctype))

                nuevalinea = True
        else:
            if ctype == "ID" and name == "":
                name = value
            if ctype in flex.token_literals:
                lines.append(sep * depth +   "<%s value=\"%s\" />" % (ctype,cnvrt(value)))
            else:
                lines.append(sep * depth +  "<%s />" % (ctype))


    if mode == "hash":
        #print "\n".join(lines)
        for row in sorted(ranges):
            output.write("\t".join([ str(x) for x in row]))
            output.write("\n")
            output.flush()
    if mode == "xml":
        for row in lines:
            output.write(row)
            output.write("\n")
            output.flush()

    return name, lines, tree['range']



def parse(data):
    global input_data
    global error_count
    global seen_tokens
    seen_tokens[:] = []
    parser.error = 0
    input_data = data
    flex.lexer.lineno = 1
    error_count = 0
    p = parser.parse(data, debug = 0, tracking = 1, tokenfunc = my_tokenfunc)
    if error_count > 0:
        print("ERRORS (%d)" % error_count)
    if p is None: return p
    try:
        p["error_count"] = error_count
    except Exception as e:
        print(e)
        return None

    if parser.error:
        return None
    return p


def main():
    global start
    parser = OptionParser()
    #parser.add_option("-f", "--file", dest="filename",
    #                  help="write report to FILE", metavar="FILE")
    parser.add_option("-O", "--output", dest="output", default = "none",
                          help="Set output TYPE: xml|hash", metavar="TYPE")
    parser.add_option("--start", dest="start", default = None,
                          help="Set start block", metavar="STMT")
    parser.add_option("-q", "--quiet",
                    action="store_false", dest="verbose", default=True,
                    help="don't print status messages to stdout")

    parser.add_option("--optdebug",
                    action="store_true", dest="optdebug", default=False,
                    help="debug optparse module")

    parser.add_option("--debug",
                    action="store_true", dest="debug", default=False,
                    help="prints lots of useless messages")


    (options, args) = parser.parse_args()
    if options.optdebug:
        print(options, args)
    if options.start:
        start = options.start
        print("Start setted to:" , start)




    def do_it():
        if options.output == "none": return
        tree_data = calctree(prog)
        if options.output == "hash":
            printtree(tree_data, mode = "hash")
        elif options.output == "xml":
            printtree(tree_data, mode = "xml")
        elif options.output == "file":
            f1_hash = open(filename+".hash","w")
            printtree(tree_data, mode = "hash", output = f1_hash)
            f1_hash.close()

            f1_xml = open(filename+".xml","w")
            printtree(tree_data, mode = "xml", output = f1_xml)
            f1_xml.close()
        elif options.output == "yaml":
            import yaml
            print(yaml.dump(tree_data['content']))

        else:
            print("Unknown outputmode", options.output)

    prog = "$$$"
    if len(args) > 0 :
        for filename in args:
            fs = filename.split("/")
            sys.stderr.write("Loading %s ..." % fs[-1])
            sys.stderr.flush()
            data = open(filename).read()
            sys.stderr.write(" parsing ...")
            sys.stderr.flush()
            prog = parse(data)
            sys.stderr.write(" formatting ...")
            sys.stderr.flush()
            if prog: do_it()
            sys.stderr.write(" Done.\n")
            sys.stderr.flush()

    else:


        line = ""
        while 1:
            try:
                line1 = input("flscript> ")
                if line1.startswith("#"):
                    comm = line1[1:].split(" ")
                    if comm[0] == "setstart":
                        start = comm[1]
                        print("Start setted to:" , start)
                    if comm[0] == "parse":
                        print()
                        prog = parse(line)
                        line = ""
                else:
                    line += line1
            except EOFError:
                break;
            line += "\n"
        print()
        prog = parse(line)
        do_it()
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







if __name__ == "__main__": main()
