#!/usr/bin/python
from __future__ import print_function
from __future__ import absolute_import
from builtins import str
from builtins import object
from optparse import OptionParser
import os, os.path, sys
import imp, traceback
from lxml import etree
try:
    from future.utils import with_metaclass
except ImportError:
    pass
    

try:
    from pineboolib.flparser import flscriptparse
except ImportError:
    import flscriptparse

USEFUL_TOKENS="ID,ICONST,FCONST,SCONST,CCONST,RXCONST".split(",")

KNOWN_PARSERS = {}
UNKNOWN_PARSERS = {}
def parse_for(*tagnames):
    global KNOWN_PARSERS
    def decorator(fn):
        for n in tagnames:
            KNOWN_PARSERS[n] = fn
        return fn
    return decorator

def parse(tagname, treedata):
    global KNOWN_PARSERS,UNKNOWN_PARSERS
    if tagname not in KNOWN_PARSERS:
        UNKNOWN_PARSERS[tagname] = 1
        fn = parse_unknown
    else:
        fn = KNOWN_PARSERS[tagname]
    return fn(tagname,treedata)


def getxmltagname(tagname):
    if tagname == "source": return "Source"
    if tagname == "funcdeclaration": return "Function"
    if tagname == "classdeclaration": return "Class"
    if tagname == "vardeclaration": return "Variable"
    return "Unknown.%s" % tagname

xml_class_types = []

class TagObjectFactory(type):
    def __init__(cls, name, bases, dct):
        global xml_class_types
        xml_class_types.append(cls)
        super(TagObjectFactory, cls).__init__(name, bases, dct)

class TagObject(with_metaclass(TagObjectFactory, object)):
    tags = []
    set_child_argn = False
    name_is_first_id = False
    debug_other = True
    adopt_childs_tags = []
    omit_tags = ['empty']
    callback_subelem = {}
    promote_child_if_alone = False

    @classmethod
    def tagname(self, tagname): return self.__name__

    @classmethod
    def can_process_tag(self, tagname): return tagname in self.tags

    def __init__(self, tagname):
        self.astname = tagname
        self.xml = etree.Element(self.tagname(tagname))
        self.xmlname = None
        self.subelems = []
        self.values = []
        if self.name_is_first_id:
            self.xml.set("name","")

    def adopt_children(self, argn, subelem):
        for child in subelem.xml.iterchildren():
            if self.set_child_argn: child.set("argn",str(argn))
            else:
                if 'argn' in child.attrib: del child.attrib['argn']
            self.xml.append(child)

    def omit_subelem(self, argn, subelem):
        return

    def is_in(self, listobj):
        return self.__class__ in listobj or self.astname in listobj

    def get(self, listobj, default = None):
        if self.__class__ in listobj: return listobj[self.__class__]
        if self.astname in listobj: return listobj[self.astname]
        return default


    def add_subelem(self, argn, subelem):
        if subelem.is_in(self.omit_tags): return self.omit_subelem(argn, subelem)
        if subelem.is_in(self.adopt_childs_tags): return self.adopt_children(argn, subelem)
        callback = subelem.get(self.callback_subelem)
        if callback: return getattr(self,callback)(argn,subelem)

        if self.set_child_argn: subelem.xml.set("argn",str(argn))
        self.xml.append(subelem.xml)
        self.subelems.append(subelem)

    def add_value(self, argn, vtype, value):
        self.values.append( (vtype, value) )
        if vtype == "ID" and self.name_is_first_id and self.xmlname is None:
            self.xmlname = value
            self.xml.set("name",value)
            return

        self.xml.set("arg%02d" % argn,vtype + ":" + repr(value))

    def add_other(self, argn, vtype, data):
        if self.debug_other:
            self.xml.set("arg%02d" % argn,vtype)

    def polish(self):
        if self.promote_child_if_alone:
            if len(self.values) == 0 and len(self.subelems) == 1:
                return self.subelems[0]
        return self


class ListObject(TagObject):
    set_child_argn = False
    debug_other = False

class NamedObject(TagObject):
    name_is_first_id = True
    debug_other = False

class ListNamedObject(TagObject):
    name_is_first_id = True
    set_child_argn = False
    debug_other = False

class TypedObject(ListObject):
    type_arg = 0
    def add_other(self, argn, vtype, value):
        if argn == self.type_arg:
            self.xml.set("type", vtype)


class Source(ListObject):
    tags = ["source","basicsource","classdeclarationsource","statement_list","statement_block"]
    adopt_childs_tags = ['source_element','statement_list','statement',"statement_block"]

class Identifier(NamedObject):
    tags = ["identifier","optid"]
    def polish(self):
        if self.xmlname is None:
            self.astname = "empty"
        return self


class Arguments(ListObject):
    tags = ["arglist"]
    adopt_childs_tags = ['vardecl_list']

class VariableType(NamedObject):
    tags = ["optvartype"]
    def polish(self):
        if self.xmlname is None:
            self.astname = "empty"
        return self

class ExtendsType(NamedObject):
    tags = ["optextends"]
    def polish(self):
        if self.xmlname is None:
            self.astname = "empty"
        return self

class Function(ListNamedObject):
    tags = ["funcdeclaration"]
    callback_subelem = ListNamedObject.callback_subelem.copy()
    callback_subelem[VariableType] = "add_vartype"

    def add_vartype(self, argn, subelem):
        self.xml.set("returns", str(subelem.xmlname))

class FunctionAnon(ListObject):
    tags = ["funcdeclaration_anon"]

class FunctionAnonExec(ListObject):
    tags = ["funcdeclaration_anon_exec"]

class Variable(NamedObject):
    tags = ["vardecl"]
    callback_subelem = NamedObject.callback_subelem.copy()
    callback_subelem[VariableType] = "add_vartype"

    def add_vartype(self, argn, subelem):
        self.xml.set("type", str(subelem.xmlname))

class DeclarationBlock(ListObject):
    tags = ["vardeclaration"]
    adopt_childs_tags = ['vardecl_list']
    def add_other(self, argn, vtype, value):
        if argn == 0:
            self.xml.set("mode", vtype)
    def polish(self):
        #if len(self.values) == 0 and len(self.subelems) == 1:
        #    self.subelems[0].xml.set("mode",self.xml.get("mode"))
        #    return self.subelems[0]
        return self

class Class(ListNamedObject):
    tags = ["classdeclaration"]
    callback_subelem = ListNamedObject.callback_subelem.copy()
    callback_subelem[ExtendsType] = "add_exttype"
    def add_exttype(self, argn, subelem):
        self.xml.set("extends", str(subelem.xmlname))

class Member(TagObject):
    debug_other = False
    set_child_argn = False
    tags = ["member_var","member_call"]
    adopt_childs_tags = ['varmemcall',"member_var","member_call"]

class ArrayMember(TagObject):
    debug_other = False
    set_child_argn = False
    tags = ["array_member"]
    adopt_childs_tags = ['variable_1',"func_call"]

class InstructionCall(TagObject):
    debug_other = False
    tags = ["callinstruction"]

class InstructionStore(TagObject):
    promote_child_if_alone = True
    debug_other = False
    tags = ["storeinstruction"]

class InstructionFlow(TypedObject):
    debug_other = True
    tags = ["flowinstruction"]

class Instruction(TagObject):
    promote_child_if_alone = True
    debug_other = False
    tags = ["instruction"]

class OpMath(TypedObject):
    debug_other = True
    tags = ["mathoperator"]

class Compare(TypedObject):
    debug_other = True
    tags = ["cmp_symbol","boolcmp_symbol"]

class FunctionCall(NamedObject):
    tags = ["funccall_1"]

class CallArguments(ListObject):
    tags = ["callargs"]

class Constant(ListObject):
    tags = ["constant"]
    def add_value(self, argn, vtype, value):
        value = str(value) #str(value,"ISO-8859-15","replace")
        if vtype == "SCONST":
            vtype = "String"
            value = value[1:-1]
            self.xml.set("delim",'"')
        if vtype == "CCONST":
            vtype = "String"
            value = value[1:-1]
            self.xml.set("delim","'")
        if vtype == "RCONST": vtype = "Regex"
        if vtype == "ICONST": vtype = "Number"
        if vtype == "FCONST": vtype = "Number"
        self.const_value = value
        self.const_type = vtype
        self.xml.set("type",vtype)
        self.xml.set("value",value)

class InlineUpdate(ListObject):
    tags = ["inlinestoreinstruction"]
    def add_other(self, argn, vtype, value):
        self.xml.set("type", vtype)
        if argn == 0:
            self.xml.set("mode", "update-read")
        if argn == 1:
            self.xml.set("mode", "read-update")

class If(ListObject):
    tags = ["ifstatement"]

class Condition(ListObject):
    tags = ["condition"]

class Else(ListObject):
    tags = ["optelse"]
    def polish(self):
        if len(self.subelems) == 0:
            self.astname = "empty"
        return self

class DictObject(ListObject):
    tags = ["dictobject_value_elemlist","dictobject_value"]
    adopt_childs_tags = ['dictobject_value_elemlist',"dictobject_value"]

class DictElem(ListObject):
    tags = ["dictobject_value_elem"]


class ExpressionContainer(ListObject):
    tags = ["expression"]
    # adopt_childs_tags = ['base_expression']

    def polish(self):
        if len(self.values) == 0 and len(self.subelems) == 1:
            #if isinstance(self.subelems[0], Constant):
            if self.subelems[0].xml.tag == "base_expression":
                self.subelems[0].xml.tag = "Expression"
                return self.subelems[0]
            else:
                self.xml.tag = "Value"

        return self

class InstructionUpdate(ListObject):
    tags = ["updateinstruction"]

class Switch(ListObject):
    tags = ["switch"]
    adopt_childs_tags = ['case_cblock_list','case_block_list']

class CaseList(ListObject):
    tags = ["case_block_list"]
    adopt_childs_tags = ['case_cblock_list','case_block_list']

class Case(ListObject):
    tags = ["case_block"]

class CaseDefault(ListObject):
    tags = ["case_default"]

class While(ListObject):
    tags = ["whilestatement"]

class For(ListObject):
    tags = ["forstatement"]

class ForInitialize(ListObject):
    tags = ["for_initialize"]

class ForCompare(ListObject):
    tags = ["for_compare"]

class ForIncrement(ListObject):
    tags = ["for_increment"]

class DoWhile(ListObject):
    tags = ["dowhilestatement"]

class ForIn(ListObject):
    tags = ["forinstatement"]

class With(ListObject):
    tags = ["withstatement"]

class TryCatch(ListObject):
    tags = ["trycatch"]

class New(ListObject):
    tags = ["new_operator"]

class Delete(ListObject):
    tags = ["deleteinstruction"]

class Parentheses(ListObject):
    tags = ["parentheses"]
    adopt_childs_tags = ['base_expression']

class OpUnary(TypedObject):
    tags = ["unary_operator"]

class OpTernary(ListObject):
    tags = ["ternary_operator"]

class OpUpdate(TypedObject):
    tags = ["updateoperator"]



# ----- keep this one at the end.
class Unknown(TagObject):
    promote_child_if_alone = True
    set_child_argn = False
    @classmethod
    def tagname(self, tagname): return tagname

    @classmethod
    def can_process_tag(self, tagname): return True
# -----------------

def create_xml(tagname):
    classobj = None
    for cls in xml_class_types:
        if cls.can_process_tag(tagname):
            classobj = cls
            break
    if classobj is None: return None
    return classobj(tagname)

def parse_unknown(tagname, treedata):
    xmlelem = create_xml(tagname)
    i = 0
    for k, v in treedata['content']:
        if type(v) is dict:
            instruction = parse(k,v)
            xmlelem.add_subelem(i, instruction)
        elif k in USEFUL_TOKENS:
            xmlelem.add_value(i, k, v)
        else:
            xmlelem.add_other(i, k, v)

        i+=1
    return xmlelem.polish()



def post_parse(treedata):
    source = parse("source",treedata)
    #print UNKNOWN_PARSERS.keys()
    return source.xml

class Module(object):
    def __init__(self, name, path):
        self.name = name
        self.path = path
    def loadModule(self):
        fp = None
        try:
            description = ('.py', 'U', imp.PY_SOURCE)
            #description = ('.pyc', 'U', PY_COMPILED)
            pathname = os.path.join(self.path, self.name)
            fp = open(pathname)
            name = self.name[:self.name.find(".")]
            # fp, pathname, description = imp.find_module(self.name,[self.path])
            self.module = imp.load_module(name, fp, pathname, description)
            result = True
        except FileNotFoundError:
            print("Fichero %r no encontrado" % self.name)
            result = False
        except Exception as e:
            print(traceback.format_exc())
            result = False
        if fp:
            fp.close()
        return result

def parseArgs(argv):
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
                    help="store XML results in PATH")

    parser.add_option("--topython",
                    action="store_true", dest="topython", default=False,
                    help="write python file from xml")

    parser.add_option("--exec-py",
                    action="store_true", dest="exec_python", default=False,
                    help="try to execute python file")

    parser.add_option("--toxml",
                    action="store_true", dest="toxml", default=False,
                    help="write xml file from qs")

    parser.add_option("--full",
                    action="store_true", dest="full", default=False,
                    help="write xml file from qs")

    parser.add_option("--cache",
                    action="store_true", dest="cache", default=False,
                    help="If dest file exists, don't regenerate it")

    (options, args) = parser.parse_args(argv)
    return (options, args)

def main():
    options, args = parseArgs(sys.argv[1:])
    execute(options,args)

def pythonify(filelist):
    options, args = parseArgs([])
    options.full = True
    if isinstance(filelist, str): filelist = [filelist]
    execute(options,filelist)
    print(filelist)



def execute(options, args):
    if options.optdebug:
        print(options, args)
    if options.full:
        execpython = options.exec_python
        options.exec_python = False
        options.full = False
        options.toxml = True
        if options.verbose: print("Pass 1 - Parse and write XML file . . .")
        try:
            execute(options,args)
        except Exception:
            print("Error parseando:");
            print(traceback.format_exc())

        options.toxml = False
        options.topython = True
        if options.verbose: print("Pass 2 - Pythonize and write PY file . . .")
        try:
          execute(options,[ arg+".xml" for arg in args])
        except Exception:
            print("Error convirtiendo:");
            print(traceback.format_exc())

        if execpython:
          options.exec_python = execpython 
          if options.verbose: print("Pass 3 - Test PY file load . . .")
          options.topython = False
          try:
            execute(options,[ (arg+".xml.py").replace(".qs.xml.py",".qs.py") for arg in args])
          except Exception:
              print("Error al ejecutar Python:");
              print(traceback.format_exc())
          
        print("Done.")

    elif options.exec_python:
        from . import qsatype
        for filename in args:
            realpath = os.path.realpath(filename)
            path, name = os.path.split(realpath)
            if not os.path.exists(realpath):
                print("Fichero no existe: %s" % name)
                continue
              
            mod = Module(name, path)
            if not mod.loadModule():
                print("Error cargando modulo %s" % name)

    elif options.topython:
        from .pytnyzer import pythonize
        import io
        if options.cache:
            args = [ x for x in args if not os.path.exists((x+".py").replace(".qs.xml.py",".qs.py"))
                        or os.path.getmtime(x) > os.path.getctime((x+".py").replace(".qs.xml.py",".qs.py")) ]
            
        nfs = len(args)
        for nf, filename in enumerate(args):
            bname = os.path.basename(filename)
            if options.storepath:
                destname = os.path.join(options.storepath,bname+".py")
            else:
                destname = filename+".py"
            destname = destname.replace(".qs.xml.py",".qs.py")
            if not os.path.exists(filename):
                print("Fichero %r no encontrado" % filename)
                continue
            if options.verbose: sys.stdout.write("Pythonizing File: %-35s . . . .        (%.1f%%)        \r" % (bname,100.0*(nf+1.0)/nfs))
            if options.verbose: sys.stdout.flush();
            old_stderr = sys.stdout
            stream = io.StringIO()
            sys.stdout = stream
            try:
                pythonize(filename, destname, destname + ".debug")
            except Exception:
                print("Error al pythonificar %r:" % filename)
                print(traceback.format_exc())
            sys.stdout = old_stderr 
            text = stream.getvalue()
            if len(text) > 2:
                print("%s: " % bname + ("\n%s: " % bname).join(text.splitlines()))
                

    else:
        if options.cache:
            args = [ x for x in args if not os.path.exists(x+".xml") 
                        or os.path.getmtime(x) > os.path.getctime(x+".xml")]
        nfs = len(args)
        for nf, filename in enumerate(args):
            bname = os.path.basename(filename)
            if options.verbose: sys.stdout.write("Parsing File: %-35s . . . .        (%.1f%%)    " % (bname,100.0*(nf+1.0)/nfs))
            if options.verbose: sys.stdout.flush();
            try:
                filecontent = open(filename,"r", encoding="latin-1").read()
            except Exception as e:
                print("Error: No se pudo abrir fichero %-35s          \n" % (repr(filename)), e)
                continue
            prog = flscriptparse.parse(filecontent)
            sys.stdout.write("\r");
            if not prog:
                print("Error: No se pudo abrir %-35s          \n" % (repr(filename)))
                continue
            if prog["error_count"] > 0:
                print("Encontramos %d errores parseando: %-35s          \n" % (prog["error_count"], repr(filename)))
                continue
            if options.toxml == False:
                # Si no se quiere guardar resultado, no hace falta calcular mas
                continue
            
            tree_data = None
            try:
                tree_data = flscriptparse.calctree(prog, alias_mode = 0)
            except Exception:
                print("Error al convertir a XML %r:" % bname)
                print("\n".join(traceback.format_exc().splitlines()[-7:]))
            
            if not tree_data:
                print("No se pudo parsear %-35s          \n" % (repr(filename)))
                continue
            ast = post_parse(tree_data)
            if ast is None:
                print("No se pudo analizar %-35s          \n" % (repr(filename)))
                continue
            if options.storepath:
                destname = os.path.join(options.storepath,bname+".xml")
            else:
                destname = filename+".xml"
            f1 = open(destname,"wb")
            f1.write(etree.tostring(ast, pretty_print = True))
            f1.close()



if __name__ == "__main__": main()
