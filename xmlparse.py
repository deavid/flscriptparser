from __future__ import print_function
from builtins import str
import xml.parsers.expat
import sys
from optparse import OptionParser
import re

elements = []
show_end = True
lasttextdata = ""
lstelements = []

def reset():
    global elements, show_end, lstelements, lasttextdata 
    elements = []
    show_end = True
    lasttextdata = ""
    lstelements = []


# 3 handler functions
def start_element(name, attrs):
    global elements, show_end, lstelements, lasttextdata 
    lstattrs=list(sorted([ "%s=%s" % (k,v) for k,v in attrs.items() ]))
    completename=name
    if len(lstattrs):
        completename+="&"+"&".join(lstattrs)
    
    show_end = False
    elements.append(completename)
    #print 'Start element:', name, attrs
    lstelements.append("/".join(elements))
    #print "/".join(elements)
    lasttextdata = ""
    
def end_element(name):
    global elements, show_end, lstelements,  lasttextdata
    lasttextdata = ""
    if show_end: 
        #print "/".join(elements) + "/"
        lstelements.append("/".join(elements) + ";")
        
    show_end = True
    elements.pop()
    #print 'End element:', name
    
def char_data(data):
    global elements, show_end, lstelements, lasttextdata
    #data = data.strip()
    lasttextdata+=data
    if lasttextdata.strip():
        #show_end = True
        lstelements.pop()
        lstelements.append("/".join(elements)+"(%s)" % repr(lasttextdata.strip()))
        
        
        #print "/".join(elements)+ "(%s)" % repr(data)



def unmap(lines):
    
    runmap = re.compile(r"^(?P<depth>/*)(?P<tagname>\w+)(?P<attrs>&[^\(]+)*(?P<txt>\(.+\))?$")
    # depthlevel
    # tagname
    elementpool = []
    text = []
    for line in lines:
        line = line.strip()
        if line[-1] == ";": continue
        rg1 = runmap.match(line)
        if not rg1:  
            print("error:")
            print(line)
            break
        
        depth = len(rg1.group('depth'))
        tagname = str(rg1.group('tagname'))
        t_attrs = rg1.group('attrs')
        attrs = []
        if t_attrs:
            lattrs = t_attrs[1:].split("&")
            for attr in lattrs:
                key, val = attr.split("=")
                attrs.append( (key,val) )
                
        t_txt = rg1.group('txt')
        txt = ""
        if t_txt:
            txt = eval(t_txt[1:-1])
        
        while depth < len(elementpool):
            toclose = elementpool.pop()
            text.append("</%s>" % toclose)
            text.append("\n" + "    " * len(elementpool))
            
        if depth == len(elementpool):
            #print depth, tagname, attrs, txt
            txtattrs = ""
            if attrs:
                for k,v in attrs:
                    txtattrs+=" %s=\"%s\"" % (k,v) 
            
            if txt:
                txt = txt.encode("utf-8")
                txt = txt.replace("&","&amp;")
                txt = txt.replace("<","&lt;")
            else:
                txt = ""
            text.append("<%s%s>%s" % (tagname, txtattrs,txt))
            elementpool.append(tagname)
                
            
        else:
            print("error:")
            print(depth, len(elementpool))
            break
            
    while len(elementpool):
        toclose = elementpool.pop()
        text.append("</%s>" % toclose)
        text.append("\n" + "    " * len(elementpool))
            
    return text


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
        print(options, args)
    if len(args) < 2:
        print("Se necesita al menos una accion y un argumento extra.")
        print("xmlparse (map|unmap) file1 [file2] [file3]")
        return
    action = args.pop(0)
    
    if action == "map":
        global lstelements
        separators = [
            "hbox",
            "vbox",
            "grid",
        ]
        r1 = re.compile("/widget")
        for fname in args:
            p = xml.parsers.expat.ParserCreate()

            p.StartElementHandler = start_element
            p.EndElementHandler = end_element
            p.CharacterDataHandler = char_data       
            fhandler = open(fname)
            fw = open(fname+".map","w")
            reset()
            p.ParseFile(fhandler)
            for t in lstelements:
                elems = t.split("/")
                lbox = []
                for n,e in enumerate(elems):
                    if e in separators: lbox.append(n)
                if len(lbox)>1:
                    nlbox = lbox[-2]
                    while len(elems[nlbox:]) < 2:
                        nlbox -= 1
                else:
                    nlbox = 0
                fw.write("/"*(len(elems)-1) + "/".join(elems[-1:])+ "\n")
                #print "/"*(len(elems)-1) + "/".join(elems[-1:])
            lstelements = []
            fhandler.close()
            fw.close()
    elif action == "unmap":
        for fname in args:
            fhandler = open(fname)
            fw = open(fname+".ui","w")
            for line in unmap(fhandler):
                fw.write(line)
            fw.close()
            fhandler.close()
        
    else:
        print("Unkown action '%s'" % action)


if __name__ == "__main__": main()