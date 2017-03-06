#!/usr/bin/python

from __future__ import print_function
from builtins import object
try:
    from json import dumps as json_dumps
    from json import loads as json_loads
except:
    from json import write as json_dumps
    from json import read as json_loads


import xml.parsers.expat
from optparse import OptionParser

#  json_string = json.dumps(python_variable)
#  python_var = json.loads("string_encoded_jsonvar")

def printr(*args):
    return
    print(args[0], end=' ')
    for arg in args[1:]:
        if type(arg) is str:
            arg=arg.encode("utf-8")
        print(repr(arg), end=' ')
    print()

def entity_rep(txt,entities=""):
    entity_list = list("&'\"<>")
    entity_dict = {
        '"' : "&quot;",
        "'" : "&apos;",
        '<' : "&lt;",
        '>' : "&gt;",
        "&" : "&amp;",
    }
    if entities == "": entities = entity_list
    entities = list(entities)
    if "&" not in entities: entities.append("&")
    
    for entity in entity_list:
        if entity not in entities: continue
        #print entity,entity_dict[entity]
        txt = txt.replace(entity,entity_dict[entity])
    return txt

class xmlElement(object):
    def __init__(self, parent, tagname, attrs = {}, ttype = "text", tdata = ""):
        self.parent = parent
            
        self.tagname = tagname
        self.attrs = attrs
        self.ttype = ttype
        self.tdata = tdata
    
        self.children = []
        
        if self.parent:
            self.depth = parent.depth + 1
            self.path = self.parent.path + [self.tagname]
            self.parent.children.append(self)
        else:
            self.depth = 0
            self.path = [self.tagname]
            
    def append(self,text):
        self.tdata += text
    
    def export(self,encoding):
        depth = self.depth
        tagname = self.tagname
        attrs = [ [k,v] for k,v in self.attrs.items() ]
        attrs.sort()
        tdata = self.tdata.strip()
        ttype = self.ttype
        
        if len(tdata) == 0:
            tdata = ""
            ttype = ""
        
        #v = [depth,tagname,attrs,ttype,tdata]
        #vt1 = json_dumps(v)
        vt2 = "%d)%s" % (depth,tagname)
        if attrs: vt2 +="\tattrs:" + json_dumps(attrs)
        if ttype: vt2 +="\t%s:%s"  % ( ttype, json_dumps(tdata))
        
        return vt2.encode(encoding)

    def exportXML(self):
        if type(self.attrs) is dict:
            attrs = [ [k,v] for k,v in self.attrs.items() ]
            attrs.sort()
        else:
            attrs = self.attrs
        
        txtattrs = ""
        
        if attrs:
            txtattrs=" "
            for key,value in attrs:
                txtattrs += '%s="%s" ' % (key,entity_rep(value,'&<"'))
                
        
        depthpad = u"    " * self.depth
        output = u""
        if self.tagname == "#comment":
                output += u"%s<!-- %s -->\n" % (depthpad, self.tdata)
        elif self.tagname[0] == "!":
                output += u"%s<!DOCTYPE %s%s>\n" % (depthpad, self.tagname[1:],txtattrs)
        elif self.children:
            output += u"%s<%s%s>\n" % (depthpad, self.tagname,txtattrs)
            for child in self.children:
                output += child.exportXML()
            
            output += u"%s</%s>\n" % (depthpad, self.tagname)
        else:
            if self.tdata == "":
                if txtattrs=="": txtattrs = " "
                output += u"%s<%s%s/>\n" % (depthpad, self.tagname,txtattrs)
            else:
                tdata = self.tdata
                if tdata.find("\n")>-1: tdata = "\n%s\n" % tdata
                if self.ttype=="cdata": tdata = "<![CDATA[%s]]>" % self.tdata
                else: tdata = entity_rep(self.tdata)
                
                output += u"%s<%s%s>%s</%s>\n" % (depthpad, self.tagname,txtattrs, tdata, self.tagname)
        
        
        return output
        
        
        
        

class JSON_Base(object):
    def __init__(self, finput, foutput, encoding):
        self.finput = finput
        self.foutput = foutput
        self.encoding = encoding
        
        self.init_vars()
        
    def process(self):
        print("Please define a process function.")
        
    def init_vars(self):
        pass
        
        

class JSON_Reverter(JSON_Base):
    def init_vars(self):
        self.cElement = None
        self.rootXML = []
        
    def processCmd(self,key,val):
        if key == "encoding":
            if self.encoding != "auto":
                self.encoding = self.encoding.upper()
                if val.upper() != self.encoding:
                    print(" ignoring %s=%s , using specified value '%s' instead" % (key,val,self.encoding))
                return
            self.encoding = val.upper()
            return
            
        print("ERROR: unknown key %s='%s'" % (key,val))
        
    def newElement(self,depth,tagname,text,ttype,attrs):
        parent = self.cElement
        if parent: parentdepth = parent.depth 
        else: parentdepth = -1
        while parent and parentdepth > depth - 1:
            parent = parent.parent
            if parent: parentdepth = parent.depth
            else: parentdepth = -1
        
        self.cElement = xmlElement(parent, tagname, attrs, ttype , text)
        if parent is None: self.rootXML.append(self.cElement)
            
            
    def process(self):
        for line in self.finput:
            line = line.strip()
            if len(line) == 0: continue
            if line[0]=="!":
                lstkeys = line[1:].split(":")
                key, val = lstkeys
                self.processCmd(key.strip(),val.strip())
                continue
                
            fields = line.split("\t")
            
            depth, tag = fields[0].split(")")
            depth = int(depth)
            text = ""
            ttype = "text"
            attrs = {}
            
            #self.foutput.write("%d\t%s\n" % (depth, tag))
            for field in fields[1:]:
                tpos = field.find(":")
                if tpos == -1: 
                    print("unexpected character:", line)
                    return
                ftype = field[:tpos]
                try:
                    fvalue = json_loads(field[tpos+1:])
                except ValueError:
                    print("ValueError:", field[tpos+1:])
                    
                #if type(fvalue) is unicode:
                #    self.foutput.write("%s = %s\n" % (ftype, fvalue.encode(self.encoding)))
                #else:
                #    self.foutput.write("%s = %s\n" % (ftype, repr(fvalue)))
                if ftype == "text": 
                    text = fvalue
                    ttype = "text"
                if ftype == "cdata": 
                    text = fvalue
                    ttype = "cdata"
                if ftype == "attrs": attrs = fvalue
            
            self.newElement(depth,tag,text,ttype,attrs)        
            
        for element in self.rootXML:
            self.foutput.write(element.exportXML().encode(self.encoding))
    
"""
    Possible Format:
    
    List-per-tag:
    [ depth, tagname, attrs, ttype, tdata ]
    
    depth: 0,1,2,3,4...N
    
    tagname: \w+ -> ElementTag
    tagname: !\w+ -> DoctypeTag
    tagname: ?\w+ -> XmlDeclTag (always: xml) (attrs = version, encoding?, standalone?)
    tagname: #\w+ -> CommentTag (always: comment) (attrs = []) (tdata = comment)
    
    attrs: dict { attr : val , attr2 : val2 }
    
    ttype: text|cdata|mixed -multiline?
    
    tdata: raw text + cdata combined.
    
    
    Problems:
    * Handling C-DATA
    * Handling multiline texts
    * Handling tabs and spaces at the start of each line of multiline text
    * Handling comments
    
    Non-treated:
    * NameSpaces 
        <edi:price xmlns:edi='http://ecommerce.example.org/schema' units='Euro'>32.18</edi:price>
        
    * Entity Declarations
        <!ENTITY name PUBLIC "public_ID" "URI">
        
    * Element Declarations
        <!ELEMENT author (#PCDATA)>
        
    * Notation Declarations
        <!NOTATION name PUBLIC "public_ID" "URI">
        
    * Attribute List Delcarations
        <!ATTLIST title 
             edition (CDATA) #REQUIRED
             type (paper|cloth|hard)"paper">
    
    
    
    
    Example 1: AbanQ UI (UTF-8)
        StartDoctypeDeclHandler: 'UI' None None 0
        EndDoctypeDeclHandler:
        StartElementHandler: 'UI' {u'version': u'3.3', u'stdsetdef': u'1'}
        CharacterDataHandler: '\n'
        StartElementHandler: 'class' {}
        CharacterDataHandler: 'formLineasAlbaranesCli'
        EndElementHandler: 'class'

    Example 2: JasperReports JRXML (UTF-8)
        XmlDeclHandler: '1.0' 'UTF-8' -1
        Unhandled data: '\n'
        StartElementHandler: 'jasperReport' {u'xmlns': u'http://jasperreports.sourceforge.net/jasperreports', u'name': u'report1', u'language': u'groovy', u'pageWidth': u'842', u'columnWidth': u'802', u'topMargin': u'20', u'rightMargin': u'20', u'bottomMargin': u'20', u'xmlns:xsi': u'http://www.w3.org/2001/XMLSchema-instance', u'leftMargin': u'20', u'xsi:schemaLocation': u'http://jasperreports.sourceforge.net/jasperreports http://jasperreports.sourceforge.net/xsd/jasperreport.xsd', u'pageHeight': u'595', u'orientation': u'Landscape'}
        CharacterDataHandler: '\n'
        CharacterDataHandler: '\t'
        StartElementHandler: 'style' {u'fontName': u'Times New Roman', u'name': u'Title', u'isBold': u'false', u'forecolor': u'#FFFFFF', u'fontSize': u'50', u'isDefault': u'false', u'pdfFontName': u'Times-Bold'}
        EndElementHandler: 'style'    
    
    Example 3: AbanQ Actions XML (ISO-8859-1)
        StartElementHandler: 'ACTIONS' {}
        CharacterDataHandler: '\n'
        CharacterDataHandler: '    '
        StartElementHandler: 'action' {}
        CharacterDataHandler: '\n'
        CharacterDataHandler: '        '
        StartElementHandler: 'name' {}
        CharacterDataHandler: 'albaranescli'
        EndElementHandler: 'name'
        CharacterDataHandler: '\n'
        CharacterDataHandler: '        '
        StartElementHandler: 'description' {}
        CharacterDataHandler: 'QT_TRANSLATE_NOOP("MetaData","Son los documentos que justifican la entrega de una mercancia a un ciente")'
        EndElementHandler: 'description'
        CharacterDataHandler: '\n'
        CharacterDataHandler: '        '
    
    Example 4: AbanQ Tables MTD (ISO-8859-1)
        StartDoctypeDeclHandler: 'TMD' None None 0
        EndDoctypeDeclHandler:
        Unhandled data: '\n'
        StartElementHandler: 'TMD' {}
        CharacterDataHandler: '\n'
        CharacterDataHandler: '    '
        StartElementHandler: 'name' {}
        CharacterDataHandler: 'facturascli'
        EndElementHandler: 'name'
        CharacterDataHandler: '\n'
        CommentHandler: 'Facturas de cliente'
        CharacterDataHandler: '    '
        StartElementHandler: 'alias' {}
        CharacterDataHandler: 'QT_TRANSLATE_NOOP("MetaData","Facturas de Clientes")'
        EndElementHandler: 'alias'
        CharacterDataHandler: '\n'
        CharacterDataHandler: '    '
        
    Example 5: AbanQ Report QRY (ISO-8859-1)
        StartDoctypeDeclHandler: 'QRY' None None 0
        EndDoctypeDeclHandler:
        Unhandled data: '\n'
        StartElementHandler: 'QRY' {}
        CharacterDataHandler: '\n'
        CharacterDataHandler: '\t'
        StartElementHandler: 'name' {}
        CharacterDataHandler: 'presupuestoscli'
        EndElementHandler: 'name'
        CharacterDataHandler: '\n'
        CharacterDataHandler: '\n'
        CharacterDataHandler: '\t'
        
    Example 6: AbanQ Report KUT (ISO-8859-1)
        XmlDeclHandler: '1.0' 'UTF-8' -1
        Unhandled data: '\n'
        StartDoctypeDeclHandler: 'KugarTemplate' 'kugartemplate.dtd' None 0
        EndDoctypeDeclHandler:
        Unhandled data: '\n'
        StartElementHandler: 'KugarTemplate' {u'TopMargin': u'50', u'PageSize': u'0', u'RightMargin': u'30', u'PageOrientation': u'0', u'BottomMargin': u'50', u'LeftMargin': u'30'}
        CharacterDataHandler: '\n'
        StartElementHandler: 'Detail' {u'Level': u'0', u'Height': u'0'}
        EndElementHandler: 'Detail'
        CharacterDataHandler: '\n'
        CharacterDataHandler: '\n'
        CharacterDataHandler: ' '
    
    

    
"""

class JSON_Converter(JSON_Base):

    def init_vars(self):
        self.real_encoding = self.getRealEncoding()
        self.xmltag = None
        self.taglist = []
        self.p = xml.parsers.expat.ParserCreate(self.real_encoding)

        self.p.StartElementHandler = self.StartElementHandler
        self.p.EndElementHandler = self.EndElementHandler
        self.p.CharacterDataHandler = self.CharacterDataHandler       
        self.p.XmlDeclHandler = self.XmlDeclHandler
        self.p.StartDoctypeDeclHandler = self.StartDoctypeDeclHandler
        self.p.EndDoctypeDeclHandler = self.EndDoctypeDeclHandler
        self.p.ElementDeclHandler = self.ElementDeclHandler
        self.p.AttlistDeclHandler = self.AttlistDeclHandler
        self.p.ProcessingInstructionHandler = self.ProcessingInstructionHandler
        self.p.CharacterDataHandler = self.CharacterDataHandler
        self.p.EntityDeclHandler = self.EntityDeclHandler
        self.p.NotationDeclHandler = self.NotationDeclHandler
        self.p.StartNamespaceDeclHandler = self.StartNamespaceDeclHandler
        self.p.EndNamespaceDeclHandler = self.EndNamespaceDeclHandler
        self.p.CommentHandler = self.CommentHandler
        self.p.StartCdataSectionHandler = self.StartCdataSectionHandler
        self.p.EndCdataSectionHandler = self.EndCdataSectionHandler
        self.p.DefaultHandler = self.DefaultHandler

    def getRealEncoding(self):
        validEncodings = ["UTF-8", "UTF-16", "ISO-8859-1"]
        self.encoding = self.encoding.upper()
        
        if self.encoding in validEncodings: return self.encoding
        if self.encoding.find("UTF")>=0:
            if self.encoding.find("8"):
                return "UTF-8"
            if self.encoding.find("16"):
                return "UTF-16"
            return "UTF-8"
            
        if self.encoding.find("ISO")>=0:
            return "ISO-8859-1"
            
        if self.encoding.find("1252")>=0:
            return "ISO-8859-1"
            
        if self.encoding.find("CP")==0:
            return "ISO-8859-1"
                
        if self.encoding.find("WIN")==0:
            return "ISO-8859-1"
            
        return "UTF-8"
                
        
    def process(self):
        self.p.ParseFile(self.finput)
        self.foutput.write(b"!encoding: "+ bytes(self.real_encoding, "UTF-8")+b"\n")
        for tag in self.taglist:
            self.foutput.write(tag.export(self.real_encoding)+b"\n")
    
    def startTag(self,*args):
        newtag = xmlElement(self.xmltag, *args)
        self.xmltag = newtag
        self.taglist.append(newtag)
        return newtag
    
    def endTag(self):
        self.xmltag = self.xmltag.parent
        return self.xmltag
    
    
        
    
    def StartElementHandler(self, name, attributes):
        printr( "StartElementHandler:", name, attributes)
        # tagname: \w+ -> ElementTag
        self.startTag(name, attributes)
        
    def CharacterDataHandler(self, data):
        printr( "CharacterDataHandler:", data)
        self.xmltag.append(data)
        
    def EndElementHandler(self, name):
        printr( "EndElementHandler:", name)
        self.endTag()

    def XmlDeclHandler(self, version, encoding, standalone):
        printr( "XmlDeclHandler:", version, encoding, standalone)
        # tagname: ?\w+ -> XmlDeclTag (always: xml) (attrs = version, encoding?, standalone?)
        attrs = { 'version' : version }
        if encoding: attrs['encoding'] = encoding
        if standalone: attrs['standalone'] = standalone
        
        self.startTag("?xml", attrs)
        
        self.endTag()
        
    def CommentHandler(self, data):
        printr( "CommentHandler:", data)
        # tagname: #\w+ -> CommentTag (always: comment) (attrs = []) (tdata = comment)
        self.startTag("#comment")
        self.xmltag.append(data)
        self.endTag()
        
        
    def StartCdataSectionHandler(self):
        printr( "StartCdataSectionHandler:")
        self.xmltag.ttype = "cdata"
        
    def EndCdataSectionHandler(self):
        printr( "EndCdataSectionHandler:")
        # se descarta el cierre...
    
    def StartDoctypeDeclHandler(self, doctypeName, systemId, publicId, has_internal_subset):
        printr( "StartDoctypeDeclHandler:", doctypeName, systemId, publicId, has_internal_subset)
        # tagname: !\w+ -> DoctypeTag
        attrs = {}
        if systemId: attrs['systemId'] = systemId
        if publicId: attrs['publicId'] = publicId
        if has_internal_subset: attrs['has_internal_subset'] = has_internal_subset
        
        self.startTag("!"+doctypeName,attrs)
        

    def EndDoctypeDeclHandler(self):
        printr( "EndDoctypeDeclHandler:")
        self.endTag()
        
    def ElementDeclHandler(self, name, model):
        printr( "ElementDeclHandler:", name, model)
        
    def AttlistDeclHandler(self, elname, attname, type, default, required):
        printr( "AttlistDeclHandler:", elname, attname, type, default, required)
        
    def ProcessingInstructionHandler(self, target, data):
        printr( "ProcessingInstructionHandler:", target, data)
        
    def EntityDeclHandler(self, entityName, is_parameter_entity, value, base, systemId, publicId, notationName):
        printr( "EntityDeclHandler:" , entityName, is_parameter_entity, value, base, systemId, publicId, notationName)
                
    def NotationDeclHandler(self, notationName, base, systemId, publicId):
        printr( "NotationDeclHandler:", notationName, base, systemId, publicId)

    def StartNamespaceDeclHandler(self, prefix, uri):
        printr( "StartNamespaceDeclHandler:", prefix, uri)

    def EndNamespaceDeclHandler(self, prefix):
        printr( "EndNamespaceDeclHandler:", prefix)
        
    def DefaultHandler(self,data):
        printr( "Unhandled data:", data)
    
    
            
   



def autodetectXmlEncoding(rawtext):
    lines = [ line.strip() for line in rawtext.split(b"\n") if line.strip() ]
    if lines[0].find(b"<!DOCTYPE UI>")>=0:
        # File is QtDesigner UI 
        return "UTF-8"
        
    if lines[0].find(b"UTF-8")>=0:
        # Unkown, standard xml (like jrxml)
        return "UTF-8"
        
    if lines[0].find(b"<ACTIONS>")>=0:
        # AbanQ actions XML
        return "ISO-8859-15"
        
    if lines[0].find(b"<!DOCTYPE TMD>")>=0:
        # AbanQ table MTD
        return "ISO-8859-15"

    if lines[0].find(b"<!DOCTYPE QRY>")>=0:
        # AbanQ report Query
        return "ISO-8859-15"

    if lines[0].find(b'<!DOCTYPE KugarTemplate SYSTEM "kugartemplate.dtd">')>=0:
        # AbanQ report Kut
        return "ISO-8859-15"
        
    if lines[0].find(b"<!DOCTYPE TS>")>=0:
        # AbanQ translations
        return "ISO-8859-15"

    try:
        import chardet
        dictEncoding = chardet.detect(rawtext)
        encoding = dictEncoding["encoding"]
        return encoding
    except ImportError:
        print("python-chardet library is not installed. Assuming input file is UTF-8.")
    #encoding=
    #UTF-8, UTF-16, ISO-8859-1 



def main():
    parser = OptionParser()
    #parser.add_option("-f", "--file", dest="filename",
    #                  help="write report to FILE", metavar="FILE")
    parser.add_option("-q", "--quiet",
                    action="store_false", dest="verbose", default=True,
                    help="don't print status messages to stdout")

    parser.add_option("--optdebug",
                    action="store_true", dest="optdebug", default=False,
                    help="debug optparse module")

    parser.add_option("--debug",
                    action="store_true", dest="debug", default=False,
                    help="prints lots of useless messages")

    parser.add_option("-E", "--encoding", dest="encoding", default = "auto",
                          help="Set encoding=ENC: auto,utf-8,iso-8859-15", metavar="ENC")

                    
    (options, args) = parser.parse_args()
    if options.optdebug:
        print(options, args)
    if len(args) < 2:
        print("xml2json needs at least an action and a file.")
        print("xml2json (revert|convert) file1 [file2] [file3]")
        return
    action = args.pop(0)
    
    if action == "convert":
        for fname in args:
            
            fhandler = open(fname,"rb")
            fw = open(fname+".json","wb")
            rawtext = fhandler.read()
            fhandler.seek(0)
            if options.encoding == "auto":
                encoding = autodetectXmlEncoding(rawtext)
            else:
                encoding = options.encoding
            jconv = JSON_Converter(fhandler, fw, encoding)
            jconv.process()
            
            fhandler.close()
            fw.close()
    elif action == "revert":
        for fname in args:
            lExt = fname.split(".")
            ext = "xml"
            if lExt[-1]=="json" and len(lExt[-2])>=1 and len(lExt[-2])<=6: 
                ext = lExt[-2]
            fhandler = open(fname)
            
            fw = open(fname+"."+ext,"w")
            jrev = JSON_Reverter(fhandler, fw, options.encoding)
            jrev.process()
            
            fw.close()
            fhandler.close()
        
    else:
        print("Unkown action '%s'" % action)









if __name__ == "__main__": main()
