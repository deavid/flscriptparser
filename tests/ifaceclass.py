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
            if not analyzeClass(code, classname):
                print "Test ifaceClass failed!"
                return False
        else:
            print "Cannot extract class name for iface variable!"
            return False
        
    else:
        print "no."
        print
        print "Bypassing test because iface wasn't found."
        return True

    print "Test ifaceClass passed!"
    return True
        
def analyzeClass(code, classname, parentlist = []):
    begin = False
    if parentlist == []: begin = True
    
    print "Analyzing classname", classname, " . . ."
    print "Is %s declared?" % classname,
    if classname not in code.byDefName:
        print "No. Can't find the class declaration in the source. Aborting."
        return False
    else:
        print "yes."
    
    cclass = code.byDefName[classname]
    parentlist.append(classname)
    if cclass.extends:
        print "class %s is a child of %s." % (classname,str(cclass.extends))
        if str(cclass.extends) == classname:
            print "%s fails in analysis because extends a class with the same name." % classname
            return False

        if str(cclass.extends) in parentlist:
            print "%s fails in analysis because extends a class already in the hierarchy." % classname
            return False

        if not analyzeClass(code, str(cclass.extends)):
            print "%s fails in analysis because its parent failed." % classname
            return False
        
    
    cclass.childclasses = []
    for name in parentlist:
        if len(cclass.childclasses) or name == classname:
            cclass.childclasses =  [name] + cclass.childclasses
    
    ### Search constructor ####
    if classname in  cclass.source.byDefName:
        print "constructor function for %s found" % classname
        constructor = cclass.source.byDefName[classname]
        cclass.constructor = constructor
    else:
        print "#WARNING# Constructor function for %s NOT found" % classname
        if cclass.extends:
            cextends = code.byDefName[str(cclass.extends)]
            if cextends.constructor:
                print "#ERROR# Parent class has one constructor and constructor function for %s NOT found!" % classname
                
            
            

    print "%s is a valid class." % (".".join(cclass.childclasses))

    return True



