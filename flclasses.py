
class cBase:
    def __init__(self):
        self.type = ("Unknown","Unknown")
        self.codedepth = 0
    def __len__(self):
        return 1;

class cBaseItem(cBase):
    def __init__(self,value):
        cBase.__init__(self)
        self.type = ("Item","Unknown")
        self.value = value

    def __str__(self):
        return str(self.value)

class cBaseItemList(cBase):
    def __init__(self,itemList,prefix,suffix):
        cBase.__init__(self)
        self.type = ("ItemList","Unknown")
        self.itemList = itemList
        self.prefix = prefix
        self.suffix = suffix

    def __str__(self):
        return str(self.prefix) + str(self.itemList) + str(self.suffix)
        

class cBaseVarSpec(cBase):
    def __init__(self,name,vartype=None,value=None):
        cBase.__init__(self)
        self.type = ("Item","Variable")
        self.value = value
        self.vartype = vartype
        self.name = name

    def __str__(self):
        txt=self.name
        if self.vartype: txt+=":"+self.vartype
        if self.value: txt+="="+str(self.value)
        return txt

    
        
class cBaseList(cBase):
    def __init__(self):
        cBase.__init__(self)
        self.type = ("List","Unknown")
        self.slice = []
        self.byType = {}
        self.bySubtype = {}
        self.byDefName = {}

    def __len__(self):
        return len(self.slice);

    def addChild(self,child):
        try:
            ctype, csubtype = child.type
        except:
            raise NameError, "Base Class doesn't have `type` atribute or is incorrect."
        self.slice.append(child)
        if not hasattr(self.byType,ctype):
            self.byType[ctype]=[]

        if not hasattr(self.bySubtype,ctype):
            self.bySubtype["%s:%s" % (ctype,csubtype)]=[]
            
        self.byType[ctype].append(child)
        self.bySubtype["%s:%s" % (ctype,csubtype)].append(child)
        
        if ctype == "Declaration":
            try:
                cname = child.name
            except:
                raise NameError, "Declaration Class doesn't have `name` atribute."
            
        try:
            child.codedepth = self.codedepth + 1
        except:
            raise NameError, "Base Class doesn't have `codedepth` atribute."
        
    def __str__(self):
        if len(self.slice) == 1:
            c = self.slice[0]
            return " " + str(c).replace("\n","\n" + "  " * c.codedepth) + " "
        txt = "\n"
        for c in self.slice:
            txt += "  " * c.codedepth + str(c).replace("\n","\n" + "  " * c.codedepth)
            txt += "\n"
        return txt
        
            
        
class cBaseListInline(cBaseList):
    def __init__(self,separator=", "):
        cBaseList.__init__(self)
        self.separator = separator

    def __str__(self):
        txt = ""
        for c in self.slice:
            txt += str(c).replace("\n","\n" + "  " * c.codedepth)
            txt += self.separator
        
        if len(self.separator) == 0:
            return txt
        else:
            return txt[:-len(self.separator)]
    
        
class cStatementList(cBaseList):
    def __init__(self):
        cBaseList.__init__(self)
        self.type = ("List","Statement")

class cBaseDecl(cBase):
    def __init__(self,name):
        cBase.__init__(self)
        self.type = ("Declaration","Unknown")
        self.name = name
        
    def __str__(self):
        return "@unknown declaration %s" % self.name


class cFuncDecl(cBaseDecl):
    def __init__(self,name,arglist,rettype,source):
        cBaseDecl.__init__(self,name=name)
        self.type = ("Declaration","Function")
        self.arglist = arglist
        self.rettype = rettype
        self.source = source
        

    def __str__(self):
        if self.rettype:
            ret=" : " + self.rettype
        else:
            ret=""
        return 'function %s(%s)%s {%s}' % (self.name,self.arglist,ret,self.source)

class cClassDecl(cBaseDecl):
    def __init__(self,name,extends,source):
        cBaseDecl.__init__(self,name=name)
        self.type = ("Declaration","Class")
        self.extends = extends
        self.source = source
        

    def __str__(self):
        if self.extends:
            ext = " extends " + self.extends
        else:
            ext = ""
            
        return 'class %s%s {%s}' % (self.name,ext,self.source)

