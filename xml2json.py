import json
import xml.parsers.expat
from optparse import OptionParser

#  json_string = json.dumps(python_variable)
#  python_var = json.loads("string_encoded_jsonvar")

def printr(*args):
    print args[0],
    for arg in args[1:]:
        if type(arg) is unicode:
            arg=arg.encode("utf-8")
        print repr(arg),
    print


class JSON_Base:
    def __init__(self, finput, foutput):
        self.finput = finput
        self.foutput = foutput
        
        self.init_vars()
        
    def process(self):
        print "Please define a process function."
        
    def init_vars(self):
        pass
    
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
        self.p = xml.parsers.expat.ParserCreate()

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
        
    def process(self):
        self.p.ParseFile(self.finput)
        
        
    def StartElementHandler(self, name, attributes):
        printr( "StartElementHandler:", name, attributes)
        
    def CharacterDataHandler(self, data):
        printr( "CharacterDataHandler:", data)
        
    def EndElementHandler(self, name):
        printr( "EndElementHandler:", name)

    def XmlDeclHandler(self, version, encoding, standalone):
        printr( "XmlDeclHandler:", version, encoding, standalone)
        
    def CommentHandler(self, data):
        printr( "CommentHandler:", data)
        
    def StartCdataSectionHandler(self):
        printr( "StartCdataSectionHandler:")
        
    def EndCdataSectionHandler(self):
        printr( "EndCdataSectionHandler:")
    
    def StartDoctypeDeclHandler(self, doctypeName, systemId, publicId, has_internal_subset):
        printr( "StartDoctypeDeclHandler:", doctypeName, systemId, publicId, has_internal_subset)

    def EndDoctypeDeclHandler(self):
        printr( "EndDoctypeDeclHandler:")
        
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
    
class JSON_Reverter(JSON_Base):
    pass






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

                    
    (options, args) = parser.parse_args()
    if options.optdebug:
        print options, args
    if len(args) < 2:
        print "xml2json needs at least an action and a file."
        print "xml2json (revert|convert) file1 [file2] [file3]"
        return
    action = args.pop(0)
    
    if action == "convert":
        for fname in args:
            
            fhandler = open(fname)
            fw = open(fname+".json","w")
            jconv = JSON_Converter(fhandler, fw)
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
            jrev = JSON_Reverter(fhandler, fw)
            jrev.process()
            
            fw.close()
            fhandler.close()
        
    else:
        print "Unkown action '%s'" % action









if __name__ == "__main__": main()