#!/usr/bin/python
# -*- coding: utf-8 -*-
# ------ Pythonyzer ... reads XML AST created by postparse.py and creates an equivalent Python file.
from __future__ import print_function
from __future__ import absolute_import
from builtins import object
from optparse import OptionParser
import os, os.path, random
from . import flscriptparse
from lxml import etree
from future.utils import with_metaclass


def id_translate(name):
    python_keywords = ['and', 'del', 'for', 'is', 'raise', 'assert', 'elif',
    'from', 'lambda', 'return', 'break', 'else', 'global', 'not', 'try',
    'class', 'except', 'if', 'or', 'while', 'continue', 'from',
    'exec', 'import', 'pass', 'yield', 'def', 'finally', 'in', 'print']
    if name in python_keywords: return name + "_"
    if name == "false": name = "False"
    if name == "true": name = "True"
    if name == "null": name = "None"
    if name == "unknown": name = "None"
    if name == "undefined": name = "None"
    if name == "this": name = "self"

    if name == "startsWith": name = "startswith"
    return name

ast_class_types = []

class ASTPythonFactory(type):
    def __init__(cls, name, bases, dct):
        global ast_class_types
        ast_class_types.append(cls)
        super(ASTPythonFactory, cls).__init__(name, bases, dct)

class ASTPython(with_metaclass(ASTPythonFactory, object)):
    tags = []
    debug_file = None
    generate_depth = 0
    numline = 0
    @classmethod
    def can_process_tag(self, tagname): return self.__name__ == tagname or tagname in self.tags

    def __init__(self, elem):
        self.elem = elem
        if self.debug_file: 
            self.internal_generate = self.generate
            self.generate = self._generate

    def debug(self, text):
        if self.debug_file is None: return
        splen = ASTPython.generate_depth
        retlen = 0
        if splen > self.generate_depth:
            retlen, splen = splen - self.generate_depth, self.generate_depth
        if retlen > 0:
            sp = " " * (splen - 1) + "<" + "-" * retlen
        else:
            sp = " " * splen 
        cname = self.__class__.__name__
        self.debug_file.write("%04d" % ASTPython.numline + sp + cname + ": " + text + "\n");
        
    def polish(self): return self

    def generate(self, **kwargs):
        yield "debug", "* not-known-seq * " + etree.tounicode(self.elem)
    def _generate(self, **kwargs):
        self.debug("begin-gen")
        ASTPython.generate_depth += 1
        self.generate_depth = ASTPython.generate_depth 
        for dtype, data in self.internal_generate(**kwargs):
            self.debug("%s: %r" % (dtype, data))
            yield dtype, data
        ASTPython.generate_depth -= 1
        self.debug("end-gen")
            
        


class Source(ASTPython):
    def generate(self, break_mode = False, include_pass = True, **kwargs):
        elems = 0
        after_lines = []
        for child in self.elem:
            #yield "debug", "<%s %s>" % (child.tag, repr(child.attrib))
            for dtype, data in parse_ast(child).generate(break_mode = break_mode, plusplus_as_instruction = True):
                if dtype == "line+1":
                    after_lines.append(data)
                    continue
                if dtype == "line":
                    elems += 1
                yield dtype, data
                if dtype == "line" and after_lines:
                    for line in after_lines:
                        elems+=1
                        yield dtype, line
                    after_lines = []
                if dtype == "break":
                    for line in after_lines:
                        elems+=1
                        yield "line", line

        for line in after_lines:
            elems+=1
            yield "line", line
        if elems == 0 and include_pass:
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
        _name = self.elem.get("name")
        if _name:
            name = id_translate(_name)
        else:
            # Anonima:
            name = "_"
        withoutself = self.elem.get("withoutself")
        
        returns = self.elem.get("returns",None)
        parent = self.elem.getparent()
        grandparent = None
        if parent is not None: grandparent = parent.getparent()
        arguments = []
        if not withoutself:
            if grandparent is not None:
                if grandparent.tag == "Class":
                    arguments.append("self")
                    if name == grandparent.get("name"):
                        name = "__init__"
            else:
                arguments.append("self")
        for n,arg in enumerate(self.elem.xpath("Arguments/*")):
            expr = []
            for dtype, data in parse_ast(arg).generate():
                if dtype == "expr":
                    expr.append(id_translate(data))
                else:
                    yield dtype, data
            if len(expr) == 0:
                arguments.append("unknownarg")
                yield "debug", "Argument %d not understood" % n
                yield "debug", etree.tostring(arg)
            else:
                if len(expr) == 1: expr += ["=","None"]
                arguments.append(" ".join(expr))



        yield "line", "def %s(%s):" % (name,", ".join(arguments))
        yield "begin", "block-def-%s" % (name)
        # if returns:  yield "debug", "Returns: %s" % returns
        for source in self.elem.xpath("Source"):
            for obj in parse_ast(source).generate(): yield obj
        yield "end", "block-def-%s" % (name)

class FunctionAnon(Function):
    pass

class FunctionCall(ASTPython):
    def generate(self, **kwargs):
        name = id_translate(self.elem.get("name"))
        parent = self.elem.getparent()
        if parent.tag == "InstructionCall":
            classes = parent.xpath("ancestor::Class")
            if classes:
                class_ = classes[-1]
                extends = class_.get("extends")
                if extends == name:
                    name = "super(%s, self).__init__" % class_.get("name")
            functions = parent.xpath("//Function[@name=\"%s\"]" % name)
            for f in functions:
                #yield "debug", "Function to:" + etree.tostring(f)
                name = "self.%s" % name
                break

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
    def generate(self, break_mode = False, **kwargs):
        main_expr = []
        for n,arg in enumerate(self.elem.xpath("Condition/*")):
            expr = []
            for dtype, data in parse_ast(arg).generate(isolate = False, ):
                if dtype == "line+1":
                    yield "debug", "Inline update inside IF condition not allowed. Unexpected behavior."
                    dtype = "line"
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
            for obj in parse_ast(source).generate(break_mode = break_mode): yield obj
            yield "end", "block-if"

        for source in self.elem.xpath("Else/Source"):
            yield "line", "else:"
            yield "begin", "block-else"
            for obj in parse_ast(source).generate(break_mode = break_mode): yield obj
            yield "end", "block-else"

class TryCatch(ASTPython):
    def generate(self, **kwargs):

        tryblock, catchblock = self.elem.xpath("Source")

        yield "line", "try:"
        yield "begin", "block-try"
        for obj in parse_ast(tryblock).generate(): yield obj
        yield "end", "block-try"

        identifier = None
        for ident in self.elem.xpath("Identifier"):
            expr = []
            for dtype, data in parse_ast(ident).generate(isolate = False):
                if dtype == "expr":
                    expr.append(data)
                else:
                    yield dtype, data
            identifier = " ".join(expr)
        if identifier:
            yield "line", "except Exception as %s:" % (identifier)
        else:
            yield "line", "except Exception:"
        yield "begin", "block-except"
        if identifier:
            # yield "line", "%s = str(%s)" % (identifier, identifier)
            yield "line", "%s = traceback.format_exc()" % (identifier)
        for obj in parse_ast(catchblock).generate(include_pass = identifier is None): yield obj
        yield "end", "block-except"


class While(ASTPython):
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

        yield "line", "while %s:" % (" ".join(main_expr))
        for source in self.elem.xpath("Source"):
            yield "begin", "block-while"
            for obj in parse_ast(source).generate(): yield obj
            yield "end", "block-while"

class DoWhile(ASTPython):
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
        # TODO .....
        key = "%02x" % random.randint(0,255)
        name1st = "s%s_dowhile_1stloop" % key
        yield "line", "%s = True" % (name1st)

        yield "line", "while %s or %s:" % (name1st, " ".join(main_expr))
        for source in self.elem.xpath("Source"):
            yield "begin", "block-while"
            yield "line", "%s = False" % (name1st)
            for obj in parse_ast(source).generate(): yield obj
            yield "end", "block-while"

class For(ASTPython):
    def generate(self, **kwargs):
        init_expr = []
        for n,arg in enumerate(self.elem.xpath("ForInitialize/*")):
            expr = []
            for dtype, data in parse_ast(arg).generate(isolate = False):
                if dtype == "expr":
                    expr.append(data)
                else:
                    yield dtype, data
            if len(expr) > 0:
                init_expr.append(" ".join(expr))
        if init_expr:
            yield "line", " ".join(init_expr)

        incr_expr = []
        incr_lines = []
        for n,arg in enumerate(self.elem.xpath("ForIncrement/*")):
            expr = []
            for dtype, data in parse_ast(arg).generate(isolate = False):
                if dtype == "expr":
                    expr.append(data)
                elif dtype in ["line","line+1"]:
                    incr_lines.append(data)
                else:
                    yield dtype, data
            if len(expr) > 0:
                incr_expr.append(" ".join(expr))


        main_expr = []
        for n,arg in enumerate(self.elem.xpath("ForCompare/*")):
            expr = []
            for dtype, data in parse_ast(arg).generate(isolate = False):
                if dtype == "expr":
                    expr.append(data)
                else:
                    yield dtype, data
            if len(expr) == 0:
                main_expr.append("True")
            else:
                main_expr.append(" ".join(expr))
        #yield "debug", "WHILE-FROM-QS-FOR: (%r;%r;%r)" % (init_expr,main_expr,incr_lines)
        yield "line", "while %s:" % (" ".join(main_expr))
        for source in self.elem.xpath("Source"):
            yield "begin", "block-for"
            for obj in parse_ast(source).generate(include_pass=False): yield obj
            if incr_lines:
                for line in incr_lines:
                    yield "line", line
            yield "end", "block-for"

class ForIn(ASTPython):
    def generate(self, **kwargs):
        list_elem, main_list = "None", "None"
        myelems = []
        for e in self.elem:
            if e.tag == "Source": break
            if e.tag == "ForInitialize": e = list(e)[0]
            expr = []
            for dtype, data in parse_ast(e).generate(isolate = False):
                if dtype == "expr":
                    expr.append(data)
                else:
                    yield dtype, data
            myelems.append(" ".join(expr))
        list_elem, main_list = myelems
        yield "debug", "FOR-IN: " + repr(myelems)
        yield "line", "for %s in %s:" % (list_elem, main_list)
        for source in self.elem.xpath("Source"):
            yield "begin", "block-for-in"
            for obj in parse_ast(source).generate(include_pass=False): yield obj
            yield "end", "block-for-in"

class Switch(ASTPython):
    def generate(self, **kwargs):
        key = "%02x" % random.randint(0,255)
        name = "s%s_when" % key
        name_pr = "s%s_do_work" % key
        name_pr2 = "s%s_work_done" % key
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
        yield "line", "%s = %s" % (name, " ".join(main_expr))
        yield "line", "%s,%s = %s,%s" % (name_pr,name_pr2, "False","False")
        for scase in self.elem.xpath("Case"):
            value_expr = []
            for n,arg in enumerate(scase.xpath("Value")):
                expr = []
                for dtype, data in parse_ast(arg).generate(isolate = False):
                    if dtype == "expr":
                        expr.append(data)
                    else:
                        yield dtype, data
                if len(expr) == 0:
                    value_expr.append("False")
                    yield "debug", "Expression %d not understood" % n
                    yield "debug", etree.tostring(arg)
                else:
                    value_expr.append(" ".join(expr))

            yield "line", "if %s == %s: %s,%s = %s,%s" % (name," ".join(value_expr),name_pr,name_pr2, "True", "True")
            yield "line", "if %s:" % (name_pr)
            yield "begin", "block-if"
            count = 0
            for source in scase.xpath("Source"):
                for obj in parse_ast(source).generate(break_mode = True):
                    if obj[0] == "break":
                        yield "line", "%s = %s # BREAK" % (name_pr,"False")
                        count += 1
                    else:
                        yield obj
                        count += 1
            if count < 1: yield "line", "pass"
            yield "end", "block-if"

        for scasedefault in self.elem.xpath("CaseDefault"):
            yield "line", "if not %s: %s,%s = %s,%s" % (name_pr2, name_pr,name_pr2, "True", "True")
            yield "line", "if %s:" % (name_pr)
            yield "begin", "block-if"
            for source in scasedefault.xpath("Source"):
                for obj in parse_ast(source).generate(break_mode = True):
                    if obj[0] == "break":
                        yield "line", "%s = %s # BREAK" % (name_pr,"False")
                    else:
                        yield obj
            yield "end", "block-if"
        # yield "line", "assert( not %s )" % name_pr
        # yield "line", "assert( %s )" % name_pr2

class With(ASTPython):
    def generate(self, **kwargs):
        key = "%02x" % random.randint(0,255)
        name = "w%s_obj" % key
        #yield "debug", "WITH: %s" % key
        variable, source = [ obj for obj in self.elem ]
        var_expr = []
        for dtype, data in parse_ast(variable).generate(isolate = False):
            if dtype == "expr":
                var_expr.append(data)
            else:
                yield dtype, data
        if len(var_expr) == 0:
            var_expr.append("None")
            yield "debug", "Expression %d not understood" % n
            yield "debug", etree.tostring(arg)

        yield "line", "%s = %s" % (name, " ".join(var_expr))

        for obj in parse_ast(source).generate(break_mode = True):
            yield obj
        yield "line", "del %s" % name

class Variable(ASTPython):
    def generate(self, force_value = False, **kwargs):
        name = self.elem.get("name")
        #if name.startswith("colorFun"): print(name)
        yield "expr", id_translate(name)
        values = 0
        for value in self.elem.xpath("Value|Expression"):
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
                parent1 = self.elem.getparent()
                parent2 = parent1.getparent()
                parent3 = parent2.getparent()
                if parent2 == "Source" and parent3 == "Class":
                    yield "expr", "None"
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
                    if data is None: raise ValueError(etree.tostring(arg))
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

class InlineUpdate(ASTPython):
    def generate(self, plusplus_as_instruction = False, **kwargs):
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
        mode = self.elem.get("mode")
        linetype = "line"
        if not plusplus_as_instruction:
            if mode == "read-update":
                linetype = "line+1"

            yield "expr", arguments[0]
        if ctype == "PLUSPLUS":
            yield linetype, arguments[0] + " += 1"
        elif ctype == "MINUSMINUS":
            yield linetype, arguments[0] + " -= 1"
        else:
            yield linetype, arguments[0] + " ?= 1"

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

class Instruction(ASTPython):
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
        if arguments:
            yield "debug", "Instruction: Maybe parse-error. This class is only for non-understood instructions or empty ones"
            yield "line", " ".join(arguments)

class InstructionFlow(ASTPython):
    def generate(self, break_mode = False, **kwargs):
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
        if ctype == "BREAK":
            kw = "break"
            if break_mode:
                yield "break", kw + " " + ", ".join(arguments)
                return
        if ctype == "CONTINUE": kw = "continue"

        if ctype == "THROW":
            yield "line", "raise Exception(" + ", ".join(arguments) + ")"
            return

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
        # Lectura del self.iface.__init
        if len(arguments) >= 3 and arguments[0:2] == ["self","iface"] and arguments[2].startswith("__"):
            # From: self.iface.__function()
            # to: super(className, self.iface).function()
            funs = self.elem.xpath("ancestor::Function")
            if funs:
                fun = funs[-1]
                name_parts = fun.get("name").split("_")
                classname = name_parts[0]
                arguments[2] = arguments[2][2:]
                arguments[0:2] = ["super(%s, %s)" % (classname,".".join(arguments[0:2]))]

        # Lectura del self.iface.__init() al nuevo estilo yeboyebo
        if len(arguments) >= 2 and arguments[0:1] == ["_i"] and arguments[1].startswith("__"):
            # From: self.iface.__function()
            # to: super(className, self.iface).function()
            funs = self.elem.xpath("ancestor::Function")
            if funs:
                fun = funs[-1]
                name_parts = fun.get("name").split("_")
                classname = name_parts[0]
                arguments[1] = arguments[1][2:]
                arguments[0:1] = ["super(%s, %s)" % (classname,".".join(arguments[0:1]))]

        replace_members = [
            "length",
            "text",
            "join",
            "date",
        ]

        for member in replace_members:
            for idx,arg in enumerate(arguments):
                if member == arg or arg.startswith(member+"("):

                    part1 = arguments[:idx]
                    try:
                        part2 = arguments[idx+1:]
                    except IndexError:
                        part2 = [] # Para los que son últimos y no tienen parte adicional
                    arguments = ["qsa(%s).%s" % (".".join(part1), arg)] + part2
        yield "expr", ".".join(arguments)

class ArrayMember(ASTPython):
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

        yield "expr", "%s[%s]" % (arguments[0],arguments[1])


class Value(ASTPython):
    def generate(self, isolate = True, **kwargs):
        if isolate: yield "expr", "("
        for child in self.elem:
            for dtype, data in parse_ast(child).generate():
                if data is None: raise ValueError(etree.tostring(child))
                yield dtype, data
        if isolate: yield "expr", ")"

class Expression(ASTPython):
    tags = ["base_expression"]
    def generate(self, isolate = True, **kwargs):
        if isolate: yield "expr", "("
        coerce_string_mode = False
        if self.elem.xpath("OpMath[@type=\"PLUS\"]"):
            if self.elem.xpath("Constant[@type=\"String\"]"):
                coerce_string_mode = True
        if coerce_string_mode:
            yield "expr", "ustr("
        for child in self.elem:
            if coerce_string_mode and child.tag == "OpMath":
                if child.get("type") == "PLUS":
                    yield "expr",","
                    continue

            for dtype, data in parse_ast(child).generate():
                yield dtype, data

        if coerce_string_mode:
            yield "expr", ")"
        if isolate: yield "expr", ")"

class Parentheses(ASTPython):
    def generate(self, **kwargs):
        yield "expr", "("
        for child in self.elem:
            for dtype, data in parse_ast(child).generate(isolate = False):
                yield dtype, data
        yield "expr", ")"

class Delete(ASTPython):
    def generate(self, **kwargs):
        yield "expr", "del"
        for child in self.elem:
            for dtype, data in parse_ast(child).generate(isolate = False):
                yield dtype, data


class OpTernary(ASTPython):
    def generate(self, isolate = False, **kwargs):
        """
            Ejemplo op. ternario
                <OpTernary>
                    <Parentheses>
                        <OpUnary type="LNOT"><Identifier name="codIso"/></OpUnary>
                        <Compare type="LOR"/><Identifier name="codIso"/><Compare type="EQ"/>
                        <Constant delim="&quot;" type="String" value=""/>
                    </Parentheses>
                    <Constant delim="&quot;" type="String" value="ES"/>
                    <Identifier name="codIso"/>
                </OpTernary>
        """
        if_cond = self.elem[0]
        then_val =  self.elem[1]
        else_val =  self.elem[2]
        yield "expr", "(" # Por seguridad, unos paréntesis
        for dtype, data in parse_ast(then_val).generate(): yield dtype, data
        yield "expr", "if"
        for dtype, data in parse_ast(if_cond).generate(): yield dtype, data
        yield "expr", "else"
        for dtype, data in parse_ast(else_val).generate(): yield dtype, data
        yield "expr", ")" # Por seguridad, unos paréntesis


class DictObject(ASTPython):
    def generate(self, isolate = False, **kwargs):
        yield "expr", "{"
        for child in self.elem:
            for dtype, data in parse_ast(child).generate():
                yield dtype, data
            yield "expr", "," # Como en Python la coma final la ignora, pues la ponemos.
        yield "expr", "}"

class DictElem(ASTPython):
    def generate(self, isolate = False, **kwargs):
        # Clave:
        for dtype, data in parse_ast(self.elem[0]).generate():
            yield dtype, data
        yield "expr", ":"
        # Valor:
        for dtype, data in parse_ast(self.elem[1]).generate():
            yield dtype, data


class OpUnary(ASTPython):
    def generate(self, isolate = False, **kwargs):
        ctype = self.elem.get("type")
        if ctype == "LNOT": yield "expr", "not"
        elif ctype == "MINUS": yield "expr", "-"
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
                ident = data[:data.find("(")]
                if ident.find(".") == -1:
                    if len(self.elem.xpath("//Class[@name='%s']" % ident)) == 0:
                        data = "qsatype." + data
                yield dtype, data


class Constant(ASTPython):
    def generate(self, **kwargs):
        ctype = self.elem.get("type")
        value = self.elem.get("value")
        self.debug("ctype: %r -> %r" % (ctype,value));
        if ctype is None or value is None:
            for child in self.elem:
                if child.tag == "list_constant":
                    # TODO/FIXME:: list_constant debe ser ELIMINADO o CONVERTIDO por postparse.py
                    # .... este generador convertirá todos los arrays en vacíos, sin importar
                    # .... si realmente tienen algo.
                    yield "expr", "[]"

                if child.tag == "CallArguments":
                    arguments = []
                    for n,arg in enumerate(child):
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

                    yield "expr", "qsatype.Array([%s])" % (", ".join(arguments))
            return
        if ctype == "String":
            delim = self.elem.get("delim")
            if delim == "'":
                yield "expr", "u'%s'" % value
            else:
                yield "expr", "u\"%s\"" % value
        elif ctype == "Number":
            value = value.lstrip("0")
            if value == "": value = "0"
            yield "expr", value
        else: yield "expr", value

class Identifier(ASTPython):
    def generate(self, **kwargs):
        name = id_translate(self.elem.get("name"))
        yield "expr", name

class OpUpdate(ASTPython):
    def generate(self, **kwargs):
        ctype = self.elem.get("type")
        if ctype == "EQUALS": yield "expr", "="
        elif ctype == "PLUSEQUAL": yield "expr", "+="
        elif ctype == "MINUSEQUAL": yield "expr", "-="
        elif ctype == "TIMESEQUAL": yield "expr", "*="
        elif ctype == "DIVEQUAL": yield "expr", "/="
        elif ctype == "MODEQUAL": yield "expr", "%="
        else: yield "expr", "OpUpdate."+ ctype

class Compare(ASTPython):
    def generate(self, **kwargs):
        ctype = self.elem.get("type")
        if ctype == "GT": yield "expr", ">"
        elif ctype == "LT": yield "expr", "<"
        elif ctype == "LE": yield "expr", "<="
        elif ctype == "GE": yield "expr", ">="
        elif ctype == "EQ": yield "expr", "=="
        elif ctype == "NE": yield "expr", "!="
        elif ctype == "EQQ": yield "expr", "is"
        elif ctype == "NEQ": yield "expr", "not is"
        elif ctype == "IN": yield "expr", "in"
        elif ctype == "LOR": yield "expr", "or"
        elif ctype == "LAND": yield "expr", "and"
        else: yield "expr", "Compare."+ctype

class OpMath(ASTPython):
    def generate(self, **kwargs):
        ctype = self.elem.get("type")
        if ctype == "PLUS": yield "expr", "+"
        elif ctype == "MINUS": yield "expr", "-"
        elif ctype == "TIMES": yield "expr", "*"
        elif ctype == "DIVIDE": yield "expr", "/"
        elif ctype == "MOD": yield "expr", "%"
        elif ctype == "XOR": yield "expr", "^"
        elif ctype == "OR": yield "expr", "or"
        elif ctype == "LSHIFT": yield "expr", "<<"
        elif ctype == "RSHIFT": yield "expr", ">>"
        elif ctype == "AND": yield "expr", "&"
        else: yield "expr", "Math."+ctype


class DeclarationBlock(ASTPython):
    def generate(self, **kwargs):
        mode = self.elem.get("mode")
        is_constructor = self.elem.get("constructor")
        #if mode == "CONST": yield "debug", "Const Declaration:"
        for var in self.elem:
            expr = []
            for dtype, data in parse_ast(var).generate(force_value=True):
                if dtype == "expr":
                    if data is None: raise ValueError(etree.tostring(var))
                    expr.append(data)
                else: yield dtype,data
            if is_constructor:
                expr[0] = "self."+expr[0]
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


def file_template(ast):
    yield "line", "# -*- coding: utf-8 -*-"
    yield "line", "from pineboolib import qsatype"
    yield "line", "from pineboolib.qsaglobals import *"
    yield "line", "import traceback"
    yield "line", ""
    sourceclasses = etree.Element("Source")
    for cls in ast.xpath("Class"):
        sourceclasses.append(cls)

    mainclass = etree.SubElement(sourceclasses,"Class",name="FormInternalObj",extends="qsatype.FormDBWidget")
    mainsource = etree.SubElement(mainclass,"Source")


    constructor = etree.SubElement(mainsource,"Function",name="_class_init")
    args = etree.SubElement(constructor,"Arguments")
    csource = etree.SubElement(constructor,"Source")

    for child in ast:
        if child.tag != "Function":
            child.set("constructor","1")
            csource.append(child)
        else:
            mainsource.append(child)

    for dtype, data in parse_ast(sourceclasses).generate():
        yield dtype, data
    yield "line", ""
    yield "line", "form = None"



def string_template(ast):
    sourceclasses = etree.Element("Source")
    for child in ast:
        child.set("withoutself","1")
        sourceclasses.append(child)

    for dtype, data in parse_ast(sourceclasses).generate():
        yield dtype, data

def write_python_file(fobj, ast, tpl=file_template):
    indent = []
    indent_text = "    "
    last_line_for_indent = {}
    numline = 0
    ASTPython.numline = 1
    last_dtype = None
    for dtype, data in tpl(ast):
        if isinstance(data, bytes): data = data.decode("UTF-8","replace")
        line = None
        if dtype == "line":
            line = data
            numline +=1
            try: lines_since_last_indent = numline - last_line_for_indent[len(indent)]
            except KeyError: lines_since_last_indent = 0
            if lines_since_last_indent > 4:
                ASTPython.numline += 1                
                fobj.write((len(indent)*indent_text) + "\n")
            last_line_for_indent[len(indent)] = numline
        if dtype == "debug":
            line = "# DEBUG:: " + data
            #print(numline, line)
        if dtype == "expr": line = "# EXPR??:: " + data
        if dtype == "line+1": line = "# LINE+1??:: " + data
        if dtype == "begin":
            #line = "# BEGIN:: " + data
            indent.append(data)
            last_line_for_indent[len(indent)] = numline
        if dtype == "end":
            if last_dtype == "begin":
                ASTPython.numline += 1
                fobj.write((len(indent)*indent_text) + "pass\n")
                last_line_for_indent[len(indent)] = numline

            if data not in ["block-if"]:
                #line = "# END:: " + data
                pass
            endblock = indent.pop()
            if endblock != data:
                line = "# END-ERROR!! was %s but %s found. (%s)" % (endblock, data,repr(indent))

        if line is not None:
            ASTPython.numline += 1
            fobj.write((len(indent)*indent_text) + line + "\n")

        if dtype == "end":
            if data.split("-")[1] in ["class","def","else","except"]:
                ASTPython.numline += 1
                fobj.write((len(indent)*indent_text) + "\n")
                last_line_for_indent[len(indent)] = numline
        last_dtype = dtype

def pythonize(filename, destfilename, debugname = None):
    bname = os.path.basename(filename)
    ASTPython.debug_file = open(debugname, "w") if debugname else None
    parser = etree.XMLParser(remove_blank_text=True)
    try:
        ast_tree = etree.parse(open(filename), parser)
    except Exception:
        print("filename:",filename)
        raise
    ast = ast_tree.getroot()
    tpl = string_template
    for cls in ast.xpath("Class"):
        tpl = file_template
        break

    f1 = open(destfilename,"w")
    write_python_file(f1,ast,tpl)
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
        print(options, args)

    for filename in args:
        if options.storepath:
            destname = os.path.join(options.storepath,bname+".py")
        else:
            destname = filename+".py"
        pythonize(filename, destname)



if __name__ == "__main__": main()
