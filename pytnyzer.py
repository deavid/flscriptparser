#!/usr/bin/python
# ------ Pythonyzer ... reads XML AST created by postparse.py and creates an equivalent Python file.
from optparse import OptionParser
import os, os.path
import flscriptparse
from lxml import etree

ast_class_types = []

class ASTPythonFactory(type):
    def __init__(cls, name, bases, dct):
        global ast_class_types
        ast_class_types.append(cls)
        super(ASTPythonFactory, cls).__init__(name, bases, dct)
        
class ASTPython(object):
    __metaclass__ = ASTPythonFactory
    tags = []
    
    @classmethod
    def can_process_tag(self, tagname): return self.__name__ == tagname or tagname in self.tags
    
    def __init__(self, elem):
        self.elem = elem

    def polish(self): return self
    
    def generate(self, **kwargs):
        yield "debug", etree.tostring(self.elem)
    

class Source(ASTPython):
    def generate(self, **kwargs):
        elems = 0
        for child in self.elem:
            #yield "debug", "<%s %s>" % (child.tag, repr(child.attrib))
            for dtype, data in parse_ast(child).generate():
                if dtype == "line":
                    elems += 1
                yield dtype, data
        if elems == 0:
            yield "line", "pass"

class Class(ASTPython):
    def generate(self, **kwargs):
        name = self.elem.get("name")
        extends = self.elem.get("extends","object")
        
        yield "line", "class %s(%s):" % (name,extends)
        yield "begin", "block-class-%s" % (name)
        for source in self.elem.xpath("Source"):
            for obj in parse_ast(source).generate(): yield obj
        yield "end", "block-class-%s" % (name)

class Function(ASTPython):
    def generate(self, **kwargs):
        name = self.elem.get("name")
        returns = self.elem.get("returns",None)
        parent = self.elem.getparent()
        grandparent = None
        if parent is not None: grandparent = parent.getparent()
        arguments = []
        
        if grandparent is not None:
            if grandparent.tag == "Class":
                arguments.append("self")
        else:                
           arguments.append("self")
        for n,arg in enumerate(self.elem.xpath("Arguments/*")):
            expr = []
            for dtype, data in parse_ast(arg).generate():
                if dtype == "expr": 
                    expr.append(data)
                else:
                    yield dtype, data 
            if len(expr) == 0:
                arguments.append("unknownarg")
                yield "debug", "Argument %d not understood" % n
                yield "debug", etree.tostring(arg)
            else:
                arguments.append(" ".join(expr))
                
                    
            
        yield "line", "def %s(%s):" % (name,", ".join(arguments)) 
        yield "begin", "block-def-%s" % (name)
        # if returns:  yield "debug", "Returns: %s" % returns
        for source in self.elem.xpath("Source"):
            for obj in parse_ast(source).generate(): yield obj
        yield "end", "block-def-%s" % (name)

class FunctionCall(ASTPython):
    def generate(self, **kwargs):
        name = self.elem.get("name")
        arguments = []
        for n,arg in enumerate(self.elem.xpath("CallArguments/*")):
            expr = []
            for dtype, data in parse_ast(arg).generate(isolate = False):
                if dtype == "expr": 
                    expr.append(data)
                else:
                    yield dtype, data 
            if len(expr) == 0:
                arguments.append("unknownarg")
                yield "debug", "Argument %d not understood" % n
                yield "debug", etree.tostring(arg)
            else:
                arguments.append(" ".join(expr))
                
                    
            
        yield "expr", "%s(%s)" % (name,", ".join(arguments)) 

class If(ASTPython):
    def generate(self, **kwargs):
        main_expr = []
        for n,arg in enumerate(self.elem.xpath("Condition/*")):
            expr = []
            for dtype, data in parse_ast(arg).generate(isolate = False):
                if dtype == "expr": 
                    expr.append(data)
                else:
                    yield dtype, data 
            if len(expr) == 0:
                main_expr.append("False")
                yield "debug", "Expression %d not understood" % n
                yield "debug", etree.tostring(arg)
            else:
                main_expr.append(" ".join(expr))
        
        yield "line", "if %s:" % (" ".join(main_expr))
        for source in self.elem.xpath("Source"):
            yield "begin", "block-if"
            for obj in parse_ast(source).generate(): yield obj
            yield "end", "block-if"
            
        for source in self.elem.xpath("Else/Source"):
            yield "line", "else:"
            yield "begin", "block-else"
            for obj in parse_ast(source).generate(): yield obj
            yield "begin", "block-end"

         
class Variable(ASTPython):
    def generate(self, force_value = False, **kwargs):
        name = self.elem.get("name")
        yield "expr", name
        values = 0
        for value in self.elem.xpath("Value"):
            values += 1
            yield "expr", "="
            expr = 0
            for dtype, data in parse_ast(value).generate(isolate = False):
                if dtype == "expr": expr += 1
                yield dtype, data
            if expr == 0:
                yield "expr", "None"
        
        dtype = self.elem.get("type",None)

        if values == 0 and force_value == True:
            yield "expr", "="
            if dtype is None:
                yield "expr", "None"
            elif dtype == "String":
                yield "expr", "\"\""
            elif dtype == "Number":
                yield "expr", "0"
            else:
                yield "expr", "qsatype.%s()" % dtype
            
        #if dtype and force_value == False: yield "debug", "Variable %s:%s" % (name,dtype)

class InstructionUpdate(ASTPython):
    def generate(self, **kwargs):
        arguments = []
        for n,arg in enumerate(self.elem):
            expr = []
            for dtype, data in parse_ast(arg).generate(isolate=False):
                if dtype == "expr": 
                    expr.append(data)
                else:
                    yield dtype, data 
            if len(expr) == 0:
                arguments.append("unknownarg")
                yield "debug", "Argument %d not understood" % n
                yield "debug", etree.tostring(arg)
            else:
                arguments.append(" ".join(expr))
                
        yield "line", " ".join(arguments)
        
class InstructionCall(ASTPython):
    def generate(self, **kwargs):
        arguments = []
        for n,arg in enumerate(self.elem):
            expr = []
            for dtype, data in parse_ast(arg).generate():
                if dtype == "expr": 
                    expr.append(data)
                else:
                    yield dtype, data 
            if len(expr) == 0:
                arguments.append("unknownarg")
                yield "debug", "Argument %d not understood" % n
                yield "debug", etree.tostring(arg)
            else:
                arguments.append(" ".join(expr))
                
        yield "line", " ".join(arguments)

class InstructionFlow(ASTPython):
    def generate(self, **kwargs):
        arguments = []
        for n,arg in enumerate(self.elem):
            expr = []
            for dtype, data in parse_ast(arg).generate(isolate=False):
                if dtype == "expr": 
                    expr.append(data)
                else:
                    yield dtype, data 
            if len(expr) == 0:
                arguments.append("unknownarg")
                yield "debug", "Argument %d not understood" % n
                yield "debug", etree.tostring(arg)
            else:
                arguments.append(" ".join(expr))

        ctype = self.elem.get("type")
        kw = ctype
        if ctype == "RETURN": kw = "return"
        if ctype == "BREAK": kw = "break"
        if ctype == "CONTINUE": kw = "continue"
        
                
        yield "line", kw + " " + ", ".join(arguments)
        
        

class Member(ASTPython):
    def generate(self, **kwargs):
        arguments = []
        for n,arg in enumerate(self.elem):
            expr = []
            for dtype, data in parse_ast(arg).generate():
                if dtype == "expr": 
                    expr.append(data)
                else:
                    yield dtype, data 
            if len(expr) == 0:
                arguments.append("unknownarg")
                yield "debug", "Argument %d not understood" % n
                yield "debug", etree.tostring(arg)
            else:
                arguments.append(" ".join(expr))
                
        yield "expr", ".".join(arguments)
        

class Value(ASTPython):
    def generate(self, isolate = True, **kwargs):
        if isolate: yield "expr", "("
        for child in self.elem:
            for dtype, data in parse_ast(child).generate():
                yield dtype, data
        if isolate: yield "expr", ")"

class Expression(ASTPython):
    def generate(self, isolate = True, **kwargs):
        if isolate: yield "expr", "("
        for child in self.elem:
            for dtype, data in parse_ast(child).generate():
                yield dtype, data
        if isolate: yield "expr", ")"

class OpUnary(ASTPython):
    def generate(self, isolate = False, **kwargs):
        ctype = self.elem.get("type")
        if ctype == "LNOT": yield "expr", "not"
        else: yield "expr", ctype
        if isolate: yield "expr", "("
        for child in self.elem:
            for dtype, data in parse_ast(child).generate():
                yield dtype, data
        if isolate: yield "expr", ")"

class New(ASTPython):
    def generate(self, **kwargs):
        for child in self.elem:
            for dtype, data in parse_ast(child).generate():
                if dtype != "expr":
                    yield dtype, data
                    continue
                if child.tag == "Identifier": data = data+"()"
                if data[:data.find("(")].find(".") == -1: data = "qsatype." + data
                yield dtype, data
        

class Constant(ASTPython):
    def generate(self, **kwargs):
        ctype = self.elem.get("type")
        value = self.elem.get("value")
        if ctype == "String": yield "expr", "\"%s\"" % value
        else: yield "expr", value

class Identifier(ASTPython):
    def generate(self, **kwargs):
        name = self.elem.get("name")
        if name == "false": name = "False"
        if name == "true": name = "True"
        if name == "null": name = "None"
        if name == "unknown": name = "None"
        if name == "this": name = "self"
        yield "expr", name

class OpUpdate(ASTPython):
    def generate(self, **kwargs):
        ctype = self.elem.get("type")
        if ctype == "EQUALS": yield "expr", "="
        elif ctype == "PLUSEQUALS": yield "expr", "+="
        elif ctype == "MINUSEQUALS": yield "expr", "-="
        elif ctype == "TIMESEQUALS": yield "expr", "*="
        elif ctype == "DIVEQUALS": yield "expr", "/="
        else: yield "expr", ctype

class Compare(ASTPython):
    def generate(self, **kwargs):
        ctype = self.elem.get("type")
        if ctype == "GT": yield "expr", ">"
        elif ctype == "LT": yield "expr", "<"
        elif ctype == "LE": yield "expr", "<="
        elif ctype == "GE": yield "expr", ">="
        elif ctype == "EQ": yield "expr", "=="
        elif ctype == "NE": yield "expr", "!="
        elif ctype == "IN": yield "expr", "in"
        else: yield "expr", ctype
        
class OpMath(ASTPython):
    def generate(self, **kwargs):
        ctype = self.elem.get("type")
        if ctype == "PLUS": yield "expr", "+"
        elif ctype == "MINUS": yield "expr", "-"
        elif ctype == "TIMES": yield "expr", "*"
        elif ctype == "DIVIDE": yield "expr", "/"
        elif ctype == "MOD": yield "expr", "%" 
        elif ctype == "XOR": yield "expr", "^"
        elif ctype == "LSHIFT": yield "expr", "<<"
        elif ctype == "RSHIFT": yield "expr", ">>"
        elif ctype == "AND": yield "expr", "&"
        else: yield "expr", ctype

        
class DeclarationBlock(ASTPython):
    def generate(self, **kwargs):
        mode = self.elem.get("mode")
        if mode == "CONST": yield "debug", "Const Declaration:"
        for var in self.elem:
            expr = []
            for dtype, data in parse_ast(var).generate(force_value=True):
                if dtype == "expr": expr.append(data)
                else: yield dtype,data
            yield "line", " ".join(expr)
                    

# ----- keep this one at the end.
class Unknown(ASTPython):
    @classmethod
    def can_process_tag(self, tagname): return True
# -----------------

def astparser_for(elem):
    classobj = None
    for cls in ast_class_types:
        if cls.can_process_tag(elem.tag):
            classobj = cls
            break
    if classobj is None: return None
    return classobj(elem)

def parse_ast(elem):
    elemparser = astparser_for(elem)
    return elemparser.polish()


def write_python_file(fobj, ast):
    indent = []
    indent_text = "    "
    for dtype, data in parse_ast(ast).generate():
        line = None
        if dtype == "line": line = data
        if dtype == "debug": line = "# DEBUG:: " + data
        if dtype == "expr": line = "# EXPR??:: " + data
        if dtype == "begin": 
            #line = "# BEGIN:: " + data
            indent.append(data)
        if dtype == "end": 
            if data not in ["block-if"]:
                #line = "# END:: " + data
                pass
            endblock = indent.pop()
            if endblock != data:
                line = "# END-ERROR!! was %s but %s found." % (endblock, data)
            
        if line is not None:
            if type(line) is unicode: line = line.encode("UTF-8","replace")
            fobj.write((len(indent)*indent_text) + line + "\n") 

        if dtype == "end": 
            if data not in ["block-if"]:
                fobj.write((len(indent)*indent_text) + "\n") 

def pythonize(filename, destfilename):
    bname = os.path.basename(filename)
    
    parser = etree.XMLParser(remove_blank_text=True)
    ast_tree = etree.parse(open(filename), parser)
    ast = ast_tree.getroot()
    
        
    f1 = open(destfilename,"w")
    write_python_file(f1,ast)
    f1.close()

def main():
    parser = OptionParser()
    parser.add_option("-q", "--quiet",
                    action="store_false", dest="verbose", default=True,
                    help="don't print status messages to stdout")

    parser.add_option("--optdebug",
                    action="store_true", dest="optdebug", default=False,
                    help="debug optparse module")
                    
    parser.add_option("--debug",
                    action="store_true", dest="debug", default=False,
                    help="prints lots of useless messages")
                    
    parser.add_option("--path",
                    dest="storepath", default=None,
                    help="store PY results in PATH")
                    

    (options, args) = parser.parse_args()
    if options.optdebug:
        print options, args
        
    for filename in args:
        if options.storepath:
            destname = os.path.join(options.storepath,bname+".py") 
        else:
            destname = filename+".py"
        pythonize(filename, destname)



if __name__ == "__main__": main()
