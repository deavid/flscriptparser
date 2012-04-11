from optparse import OptionParser
import flscriptparse
from lxml import etree
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
        
class TagObject(object):
    __metaclass__ = TagObjectFactory
    tags = []
    set_child_argn = True
    name_is_first_id = False
    debug_other = True
    adopt_childs_tags = []
    omit_tags = ['empty']
    callback_subelem = {}
    
    @classmethod
    def tagname(self, tagname): return self.__name__
    
    @classmethod
    def can_process_tag(self, tagname): return tagname in self.tags
    
    def __init__(self, tagname):
        self.astname = tagname
        self.xml = etree.Element(self.tagname(tagname))
        self.xmlname = None
        if self.name_is_first_id:
            self.xml.set("name","")
    
    def adopt_children(self, argn, subelem):
        for child in subelem.xml.iterchildren():
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
    
    def add_value(self, argn, vtype, value):
        if vtype == "ID" and self.name_is_first_id and self.xmlname is None:
            self.xmlname = value
            self.xml.set("name",value)
            return
            
        self.xml.set("arg%02d" % argn,vtype + ":" + repr(value))
    
    def add_other(self, argn, vtype, data):
        if self.debug_other:
            self.xml.set("arg%02d" % argn,vtype)
    
    def polish(self):
        return


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

class StatementList(ListObject):
    tags = ["statement_list"]
    adopt_childs_tags = ['statement']

class Instruction(ListObject):
    tags = ["instruction"]
    adopt_childs_tags = ['base_instruction']


class Source(ListObject):
    tags = ["source","basicsource"]
    adopt_childs_tags = ['source_element','statement_list']

class Identifier(NamedObject):
    tags = ["identifier"]


class Class(ListNamedObject):
    tags = ["classdeclaration"]

class Arguments(ListObject):
    tags = ["arglist"]
    adopt_childs_tags = ['vardecl_list']

class VariableType(NamedObject):
    tags = ["optvartype"]
    def polish(self):
        if self.xmlname is None:
            self.astname = "empty"

class Function(ListNamedObject):
    tags = ["funcdeclaration"]
    callback_subelem = ListNamedObject.callback_subelem.copy()
    callback_subelem[VariableType] = "add_vartype"
    
    def add_vartype(self, argn, subelem):
        self.xml.set("returns", str(subelem.xmlname))

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
    

class Unknown(TagObject):
    set_child_argn = False
    @classmethod
    def tagname(self, tagname): return tagname
    
    @classmethod
    def can_process_tag(self, tagname): return True


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
    xmlelem.polish()
    return xmlelem



def post_parse(treedata):
    source = parse("source",treedata)
    #print UNKNOWN_PARSERS.keys()
    return source.xml


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
                    

    (options, args) = parser.parse_args()
    if options.optdebug:
        print options, args
        
    for filename in args:
        prog = flscriptparse.parse(open(filename).read())                      
        tree_data = flscriptparse.calctree(prog, alias_mode = 0)
        ast = post_parse(tree_data)
        
        print etree.tostring(ast, pretty_print = True)



if __name__ == "__main__": main()
