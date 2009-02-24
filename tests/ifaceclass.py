import traceback,sys


def do_test(code):
    print "Starting iface Class test . . ."
    print    
    print "Is iface declared?",
    if "iface" in code.byDefName:
        classname = None
        iface = code.byDefName["iface"]
        print "yes."
        print "iface type is %s/%s . . ." % iface.type,
        if iface.type != ("Declaration" , "Variable"):
            print " which differs from desired value!"
            return False
        print " ok."
        print "Content: ", iface.value
        vtype, vsubtype = iface.value.type
        if iface.value.type == ("List","Expression"):
            expression = iface.value.slice
            if len(expression) == 2:
                if str(expression[0]) == "new":
                    if expression[1].type == ("Item", "FuncCall"):
                        if str(expression[1].arglist) != "this":
                            print "`this` must be the olny arg passed to the constructor!"
                            return False
                            
                        classname = expression[1].name
        
        if classname:
            return analyzeClass(classname)
        else:
            print "Cannot extract class name for iface variable!"
            return False
        
    else:
        print "no."
        print
        print "Bypassing test because iface wasn't found."
        return True
        
def analyzeClass(classname):
    print "Analyzing classname", classname, " . . ."
    return True



