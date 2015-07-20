from __future__ import print_function
from builtins import str
from builtins import object
debug = 0

class cBase(object):
    def __init__(self):
        self.type = ("Unknown","Unknown")
        self.codedepth = 0

    def setSubtype(self,newsubtype):
        x, y = self.type
        self.type = (x,newsubtype)

    def setType(self,newtype):
        x, y = self.type
        self.type = (newtype,y)

    def addCodeDepth(self):
        self.codedepth += 1

    def __len__(self):
        return 1;

class cBaseItem(cBase):
    def __init__(self,value):
        cBase.__init__(self)
        self.type = ("Item","Unknown")
        self.value = value

    def __str__(self):
        if debug > 0 and debug < 1 and self.type == ("Item","Unknown"): return "*" + str(self.value) + "?"
        return str(self.value)

class cBaseItemList(cBase):
    def __init__(self,itemList,prefix,suffix,subtype="Unknown"):
        cBase.__init__(self)
        self.type = ("ItemList",subtype)
        if not isinstance(itemList,cBaseList):
            iList = cBaseListInline()
            iList.addAuto(itemList,subtype=subtype)
            itemList = iList
            t,st = itemList.slice[0].type
            #itemList.setSubtype(st)
            itemList.setSubtype("OneItem")


        if not isinstance(itemList,cBaseList):
            raise NameError("itemList no es un cBaseList: %s" % repr(itemList))
        self.itemList = itemList
        self.prefix = prefix
        self.suffix = suffix
        if subtype=="Declaration":
            for item in self.itemList.slice:
                ctype, csubtype = item.type
                ctype = subtype
                item.type = (ctype, csubtype)

    def __str__(self):
        global debug
        txt = str(self.prefix) + str(self.itemList) + str(self.suffix)
        txt = txt.strip()
        if debug>=2:
            txt = "{%s/%s:" % self.itemList.type + txt + "}"
        return txt


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
        self.hidden = []
        self.byType = {}
        self.bySubtype = {}
        self.byDefName = {}

    def __len__(self):
        return len(self.slice);

    def includeItem(self,child):
        if not isinstance(child,cBase):
            raise NameError("Child is not an instance of Base Class!")

        try:
            ctype, csubtype = child.type
        except:
            raise NameError("Base Class doesn't have `type` atribute or is incorrect.")
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
                raise NameError("Declaration Class doesn't have `name` atribute.")

            if cname in self.byDefName:
                print("#WARNING# Variable %s found, but previously defined in this block"  % cname)
                # self.byDefName[cname]=None
            else:
                self.byDefName[cname]=child
        try:
            child.addCodeDepth()
        except:
            print(repr(child))
            raise NameError("Base Class doesn't have `addCodeDepth` function.")

        if isinstance(child,cBaseItemList):
            sslice = child.itemList.slice[:]
            for e in child.itemList.hidden:
                sslice.remove(e)


            for item in sslice:
                itype, isubtype = item.type
                if not isinstance(item,cBaseItemList):
                    self.includeItem(item)
                    #self.hidden.append(item)

    def addCodeDepth(self):
        cBase.addCodeDepth(self)
        sslice = self.slice[:]

        for e in self.hidden:
            sslice.remove(e)

        for child in sslice:
            child.addCodeDepth()



    def addAuto(self,element,subtype=None):
        if not isinstance(element,cBase):
            element = cBaseItem(element)
            if subtype:
                element.setSubtype(subtype)

        self.addChild(element)

    def addChild(self,child,hidden=False):
        self.includeItem(child)
        self.slice.append(child)
        if hidden: self.hidden.append(child)

    def __str__(self):
        global debug
        sslice = self.slice[:]

        for e in self.hidden:
            sslice.remove(e)


        if debug>=1:
            txt = "\n"
            # --------- DEBUG OUTPUT VARDECL ---------
            if len(self.byDefName)>0:
                txt += "  " * self.codedepth + "  /** Declared vars: "
                for definition in self.byDefName:
                    txt += definition + "; "
                txt += "**/\n"
            n=0
            for c in sslice:
                t1, t2 = c.type
                n+=1
                txt += "%-17s:%d" % ("%-8s/%-8s" % (t1[:8],t2[:8]),n)+ ">" + ". " * c.codedepth + str(c)
                txt += "\t<%d:\n" % n
            return txt



        if len(sslice) == 1:
            c = str(sslice[0])
            if "\n" not in c:
                return " " + c + " "
        txt = "\n"

        #for child in self.slice:
        #    if str(child.type[0]) != "ItemList":
        #        txt += str(child.type) + "\n"
        #        txt += str(child) + "\n"
        #        txt += "____"+ "\n"

        lastmargin = 0
        for c in sslice:
            t1, t2 = c.type
            line = "    " + str(c).replace("\n","\n    ")
            linecount = line.count("\n")
            margin = 0
            if linecount>2: margin += 1
            if linecount>25: margin += 1
            if linecount>50: margin += 1
            topmargin = margin - lastmargin
            if topmargin < 0: topmargin = 0
            txt += "\n" * topmargin + line + "\n" * (margin+1)
            lastmargin = margin
        return txt



class cBaseListInline(cBaseList):
    def __init__(self,separator=", "):
        cBaseList.__init__(self)
        self.separator = separator

    def __str__(self):
        global debug
        txt = ""
        for c in self.slice:
            if debug>=3:
                txt += "[%s/%s: " % c.type

            txt += str(c)
            if debug>=3:
                txt += "]"

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
        if not isinstance(source,cBaseList):
            iList = cBaseList()
            iList.addAuto(source)
            source = iList


        if not isinstance(source,cBaseList):
            raise NameError("source no es un cBaseList: %s" % repr(source))

        self.source = source

    def addCodeDepth(self):
        cBase.addCodeDepth(self)
        try:
            self.source.addCodeDepth()
        except:
            import traceback,sys
            print("Exception in user code:")
            print('-'*60)
            traceback.print_exc(file=sys.stdout)
            print('-'*60)




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
        self.childclasses = None
        self.constructor = None
        if not isinstance(source,cBaseList):
            iList = cBaseList()
            iList.addAuto(source)
            source = iList


        if not isinstance(source,cBaseList):
            raise NameError("source no es un cBaseList: %s" % repr(source))
        self.source = source

    def addCodeDepth(self):
        cBase.addCodeDepth(self)
        try:
            self.source.addCodeDepth()
        except:
            import traceback,sys
            print("Exception in user code:")
            print('-'*60)
            traceback.print_exc(file=sys.stdout)
            print('-'*60)

    def __str__(self):
        if self.extends:
            ext = " extends " + self.extends
        else:
            ext = ""

        return 'class %s%s {%s}' % (self.name,ext,self.source)

