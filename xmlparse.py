import xml.parsers.expat
import sys
from optparse import OptionParser
import re
elements = []
show_end = True
lstelements = []

# 3 handler functions
def start_element(name, attrs):
    global elements, show_end, lstelements
    lstattrs=list(sorted([ "%s=%s" % (k,v) for k,v in attrs.iteritems() ]))
    completename=name
    if len(lstattrs):
        completename+="?"+"&".join(lstattrs)
    
    show_end = False
    elements.append(completename)
    #print 'Start element:', name, attrs
    lstelements.append("/".join(elements))
    #print "/".join(elements)
    
def end_element(name):
    global elements, show_end, lstelements
    if show_end: 
        #print "/".join(elements) + "/"
        lstelements.append("/".join(elements) + "/")
        
    show_end = True
    elements.pop()
    #print 'End element:', name
    
def char_data(data):
    global elements, show_end, lstelements
    #data = data.strip()
    if data.strip():
        #show_end = True
        txt = lstelements.pop()
        lstelements.append(txt+"(%s)" % repr(data))
        
        
        #print "/".join(elements)+ "(%s)" % repr(data)




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
        
    p = xml.parsers.expat.ParserCreate()

    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data       
    global lstelements
    r1 = re.compile("/widget")
    for fname in args:
        fhandler = open(fname)
        p.ParseFile(fhandler)
        for t in lstelements:
            gl = r1.split(t)
            if len(gl)>1: 
                print "(..%d..)%s" % (len(gl)-1,gl[-1])
            else:
                print t
        lstelements = []
        fhandler.close()


if __name__ == "__main__": main()