from __future__ import print_function
from __future__ import division
from builtins import zip
from builtins import range
from past.utils import old_div
from builtins import object
import os, os.path, sys
import math
from optparse import OptionParser
import difflib
import re

class processedFile(object):
    def __init__(self, filename, debug = False):
        self.debug = debug
        self.table = {}    # Carga literal de la lista de hashes, pk: (startbyte, endbyte) = csvrow
        self.idxdepth = {}
        self.idxtree = {}  # pk: objnum (1.5.5.1.1) = (startbyte, endbyte)
        self.hashes = {}
        self.list_hashes = []
        self.filename = filename
        self.cacheFullQname = {}
        self.processHashFile()
        self.indexNames()
        self.computeSortedBlocks()

    def processHashFile(self):
        self.cacheFullQname = {}
        self.table, self.idxdepth,self.idxtree, self.hashes, self.list_hashes = process(self.filename+".hash")


    def indexNames(self):
        self.names = {}
        self.sortedNames = []
        for pk in self.idxtree:
            if len(pk) > 1: continue
            name = self.fullQName(pk)
            if name not in self.names: self.names[name] = []
            self.names[name].append(pk)
            self.sortedNames.append((self.idxtree[pk],name))

        self.sNames = set(self.names.keys())

    def Qname(self,p):
        row = self.table[self.idxtree[p]]
        return row["name"]


    def fullQName(self,p):
        dcache = self.cacheFullQname
        if p not in dcache:
            name=[]

            for n in range(len(p)):
                ps1 = p[:n+1]
                name.append(self.Qname(ps1))
            fullname = "/".join(name)
            dcache[p] = fullname
        else:
            fullname = dcache[p]

        return fullname

    def computeSortedBlocks(self, fout=None):
        self.computedBlocks = []
        if fout is None:
            fout = open(self.filename + ".blocks","w")

        antdesde, anthasta = 0 , -1
        fB = open(self.filename)
        pos = 0
        linePosChar = [pos]
        fB.seek(0)
        line = fB.readline()
        while line:
            pos += len(line)
            linePosChar.append(pos)
            line = fB.readline()
        linenum = 0
        self.linePosChar = linePosChar
        for pk, bl_name in list(sorted(self.sortedNames))+[((None,None),None)]:
            desde, hasta = pk
            if desde is None or desde >= anthasta +1:

                bdesde = anthasta + 1
                fB.seek(bdesde)
                if desde:
                    bhasta = desde - 1
                    sB = fB.read((bhasta-bdesde)+1)
                else:
                    sB = fB.read()
                    bhasta = bdesde + len(sB) -1


                while linenum < len(linePosChar) and linePosChar[linenum+1]<=bdesde: linenum += 1
                startline = linenum
                linesize=linePosChar[startline] - linePosChar[startline-1]
                curpos = bdesde  - linePosChar[startline-1]
                #if curpos != linesize: print "****", linesize, curpos


                while linenum < len(linePosChar) and linePosChar[linenum+1]<=bhasta: linenum += 1
                endline = linenum
                #while startline > 1 and linePosChar[startline-1]-bdesde >=-2: startline-=1

                #print linePosChar[startline-1]-bdesde, linePosChar[startline]-bdesde, linePosChar[startline+1]-bdesde

                #print (startline, endline), "BLOCK", (linePosChar[startline], linePosChar[endline]), (bdesde , bhasta), (bhasta-bdesde)+1

                #print "<<<<"
                mode = ""
                nline = startline
                beginline = startline
                bblocks = []
                blockdesc = []
                if len(sB.splitlines(1)) != endline-startline+1:
                    print(startline, endline, repr(sB))
                    print(linePosChar[endline-1]-bhasta, linePosChar[endline]-bhasta, linePosChar[endline+1]-bhasta)

                    print("Block lines doesnt match:", len(sB.splitlines(1)), endline-startline, startline, endline)
                    print(linePosChar[startline-2:startline+3],bdesde)
                    print(linePosChar[endline-2:endline+3],bhasta)
                    print(repr(sB.splitlines(1)))
                for line in sB.splitlines(1):
                    nline += 1
                    if line[-1]!='\n': break
                    ltype = "junk"
                    isseparator = re.match(r'[ \t]*\n',line)
                    iscommentline1 = re.match(r'[ \t]*//.+\n',line)
                    iscommentline2 = re.match(r'[ \t]*/\*.+\*/\n',line)
                    iscommentbegin = re.match(r'[ \t]*/\*.+\n',line)
                    iscommentend = re.match(r'.+\*/[ \t]*\n',line)



                    if isseparator: ltype = "separator"
                    elif iscommentline1: ltype = "comment_inline"
                    elif iscommentline2: ltype = "comment_block_inline"
                    elif iscommentbegin: ltype = "comment_block"
                    elif iscommentend: ltype = "comment_blockend"
                    #else:  print "junk?", line,

                    if mode == "comment_block" and ltype == "comment_blockend":
                        mode = "comment_blockend"

                    if mode == "comment_block" and ltype != "comment_blockend":
                        ltype = "comment_block"


                    if mode != ltype:
                        if mode:
                            if mode == "comment_blockend":
                                mode = "comment_block"
                            thisblock = ( (beginline, nline-1), ""+mode , ".".join(blockdesc)[:32])
                            blockdesc = []
                            bblocks.append(thisblock)
                        mode = ltype
                        beginline = nline - 1

                    words = re.split(r'\W+',line)
                    if words:
                        text = " ".join(words)
                        text = text.strip()
                        text = text.replace(" ", "-")
                        if len(text)>1:
                            blockdesc.append(text)

                if mode:
                    if mode == "comment_blockend":
                        mode = "comment_block"

                    thisblock = ( (beginline, nline),""+mode, ".".join(blockdesc)[:32] )
                    bblocks.append(thisblock)
                    blockdesc = []
                    #print ltype, line,

                for lines, bname, desc in bblocks:
                    #print lines, " ", "%s:%s" % (bname, desc)
                    startline, endline = lines
                    name =  "#..%s:%s" % (bname, desc)

                    self.computedBlocks.append((startline, endline,name))
                    fout.write("%d\t%d\t%s\n" % (startline, endline,name))
                    #print "#..%s:%s" % (bname, desc)
                #print sB,
                #print ">>>>"
            if desde is None: break
            initline = linenum
            while linenum < len(linePosChar) and  linePosChar[linenum+1]<desde+2: linenum += 1
            startline = linenum
            while linenum < len(linePosChar) and linePosChar[linenum]<hasta+1: linenum += 1
            #linenum += 1
            endline = linenum
            if linePosChar[startline] - desde != 0 or linePosChar[endline] - hasta < 1 or linePosChar[endline] - hasta > 2:
                print(linePosChar[startline] - desde,  linePosChar[endline-1] - hasta, linePosChar[endline] - hasta, bl_name)
            name = bl_name
            #print (startline, endline), name, (linePosChar[startline], linePosChar[endline]), pk, (hasta-desde)+1
            self.computedBlocks.append((startline, endline,name))
            fout.write("%d\t%d\t%s\n" % (startline, endline,name))
            #print "%s" % name
            antdesde, anthasta = pk
            if anthasta <= linePosChar[linenum-1] + 1:
                anthasta = linePosChar[linenum-1] + 1
            elif anthasta <= linePosChar[linenum] + 1:
                anthasta = linePosChar[linenum] + 1

        fB.close()
        fout.close()


def linejunk(line):
    line = line.strip()
    if len(line)<4: return True
    if line[2] == "//": return True
    return False

def charjunk(char):
    junk = [" ", "\t"]
    if char in junk: return True
    return False

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

    filenames = [x for x in args if os.path.isfile(x)]
    not_a_file = set(args) - set(filenames)
    if len(not_a_file):
        print("WARNING: Not a file:", ", ".join(not_a_file))

    if len(filenames):
        pfiles = []
        for file1 in filenames:
            #print "File:", file1
            pf = processedFile(file1, debug = options.debug)
            pfiles.append(pf)
        #pfA = pfiles[0]
        #for pfB in pfiles[1:]:
        #    feq = FindEquivalences(pfA, pfB)

def tree_parents(pk):
    parents = []
    while (len(pk)>0):
        parents.append(pk)
        pk = pk[:-1]
    return parents

class FindEquivalences(object):
    def __init__(self,pfA, pfB, autoCompute = True):
        self.equivalences = {}
        self.parent_equivalences = {}
        self.max_known_eq = {}
        self.pfA, self.pfB = pfA, pfB
        if autoCompute: self.compute()

    def compute(self):
        print("Finding equivalences between A (%s) -> B (%s):" % (
                self.pfA.filename,
                self.pfB.filename
                ))
        print("Modified names:")
        commonNames = sorted(list(self.pfA.sNames & self.pfB.sNames))
        for name in commonNames:
            if len(self.pfA.names[name]) > 1 or len(self.pfB.names[name]) > 1:
                print("-", name,"(%d,%d)" % (len(self.pfA.names[name]),len(self.pfB.names[name])))
            else:
                keyA = self.pfA.idxtree[self.pfA.names[name][0]]
                rowA = self.pfA.table[keyA]
                keyB = self.pfB.idxtree[self.pfB.names[name][0]]
                rowB = self.pfB.table[keyB]
                if rowA['hash'] != rowB['hash']:
                    print("###", name,"###")
                    fileA = self.pfA.filename.replace(".hash","")
                    fileB = self.pfB.filename.replace(".hash","")
                    if os.path.isfile(fileA) and os.path.isfile(fileB):
                        fA = open(fileA)
                        fA.seek(keyA[0])
                        sA = fA.read(keyA[1]-keyA[0]+1)
                        fA.close()

                        fB = open(fileB)
                        fB.seek(keyB[0])
                        sB = fB.read(keyB[1]-keyB[0]+1)
                        fB.close()

                        sA = sA.replace("\t", "        ")
                        sB = sB.replace("\t", "        ")
                        lines = list(difflib.ndiff(sA.splitlines(1), sB.splitlines(1),linejunk,charjunk))
                        modifiedlines = []
                        for n,line in enumerate(lines):
                            if line[0] != " ":
                                modifiedlines.append(n)
                        ml = 0
                        omit = []
                        Context = 3
                        n = 0
                        for line in lines:
                            d = []
                            for m in modifiedlines:
                                dt = abs(m-n)
                                d.append(dt)
                                if dt < Context: break
                            dmin = min(d)
                            if dmin < Context:
                                if len(omit) :
                                    if len(omit)>= Context:
                                        for line in omit:
                                            if line[0] in (' ','+'): n+=1
                                        print("   ", "(... %d lines ommitted ...)" % len(omit))
                                    else:
                                        for line in omit:
                                            if line[0] in (' ','+'): n+=1
                                            print("%03d" % n , line, end=' ')
                                    omit = []
                                if line[0] in (' ','+'):
                                    n+=1
                                    print("%03d" % n , line, end=' ')
                                else:
                                    print("%03d" % (n+1) , line, end=' ')
                            else:
                                omit.append(line)
                        if len(omit) :
                            if len(omit)>= Context:
                                for line in omit:
                                    if line[0] in (' ','+'): n+=1
                                print("   ", "(... %d lines ommitted ...)" % len(omit))
                            else:
                                for line in omit:
                                    if line[0] in (' ','+'): n+=1
                                    print("%03d" % n , line, end=' ')
                            omit = []
                        print()
                    else:
                        print("(diff ommitted because we couldn't find original files)")

        print()
        print("Deleted names:")
        deletedNames = sorted(list(self.pfA.sNames - self.pfB.sNames))
        for name in deletedNames:
            print("-", name)
        print()
        print("Added names:")
        addedNames = sorted(list(self.pfB.sNames - self.pfA.sNames))
        for name in addedNames:
            print("-", name)
        print()

        return






        for key in self.pfA.list_hashes:
            if key in self.pfB.hashes:
                lpkA = self.pfA.hashes[key]
                lpkB = self.pfB.hashes[key]
                self.addEquivalences(lpkA,lpkB)
            #    print "Found:", self.pfA.hashes[key] , "==>", self.pfB.hashes[key]
            #else:
            #    print "Lost:", self.pfA.hashes[key] , "==>", "???"

        for pkA in self.pfA.idxtree:
            parentA = pkA[:-1]
            if pkA not in self.equivalences:
                self.equivalences[pkA] = {}
            if parentA:
                if parentA not in self.parent_equivalences:
                    self.parent_equivalences[parentA] = []

        for pkA in sorted(self.pfA.idxtree):
            parentsA = tree_parents(pkA)
            for pkB, punt in self.equivalences[pkA].items():
                if len(pkA) != len(pkB): continue
                parentsB = tree_parents(pkB)
                parentsAB = list(zip(parentsA,parentsB))
                for pA, pB in parentsAB:
                    sz2a, sz2b = self.pfA.idxtree[pkA]
                    sz2 = sz2b - sz2a + 1
                    sz1a, sz1b = self.pfA.idxtree[pA]
                    sz1 = sz1b - sz1a + 1
                    lev2 = 1.0 + old_div(sz1, float(sz2))
                    #lev2 = 2**(len(pkA) - len(pA))
                    #lev2_list = [ pC for pC in self.pfA.idxtree if len(pC) >= len(pA) and pC[:len(pA)] == pA ]
                    #lev2_plist = set([])
                    #for l in lev2_list:
                    #    lev2_plist |= set(tree_parents(l)[1:])
                    #lev2 = len(set(lev2_list) - set(lev2_plist))

                    pEq = (pB, old_div(float(punt),lev2))
                    if pA not in self.parent_equivalences:
                        self.parent_equivalences[pA] = []
                    self.parent_equivalences[pA].append(pEq)

        norepeat = (0,)
        self.parent_equivalences2 = {}
        for pA in sorted(self.parent_equivalences):
            count = {}
            if pA[:len(norepeat)] == norepeat: continue
            for pB, punt in self.parent_equivalences[pA]:
                if pB not in count: count[pB] = 0
                count[pB] += punt
            rcount = []
            ppA = pA[:-1]
            if ppA in self.parent_equivalences2:
                ppB = self.parent_equivalences2[ppA]
            else:
                ppB = None

            rowA = self.pfA.table[self.pfA.idxtree[pA]]
            for key, punt in count.copy().items():
                if ppB and key[:-1] != ppB: continue
                rowB = self.pfB.table[self.pfB.idxtree[pB]]
                nameA = self.pfA.fullQName(pA) #rowA['name'].split(":")
                nameB = self.pfB.fullQName(pB) #rowB['name'].split(":")
                s = difflib.SequenceMatcher()
                s.set_seqs(nameA,nameB)
                t = s.quick_ratio()
                t -= 0.8
                if t < 0: t = 0
                t *= 10.0
                punt *= t
                #if nameA[0] != nameB[0]: punt /=3.0
                #if nameA[1] != nameB[1]: punt /=1.0+len(nameA[1]) / 40.0+len(nameB[1]) / 40.0
                if punt >= 0.50:
                    rcount.append((round(punt*100),key))

            if len(rcount):
                punt, pB = max(rcount)
                self.parent_equivalences2[pA] = pB
                rowB = self.pfB.table[self.pfB.idxtree[pB]]
                print("parent:", pA, self.pfA.fullQName(pA), "%d%%\t" % punt, pB, len(rcount) , self.pfB.fullQName(pB))
                if punt > 100:
                    norepeat = pA
            else:
                if len(pA) == 1:
                    print("parent:", pA, self.pfA.fullQName(pA), "0%\t  ???")

        """
        norepeat = (0,)
        prevprint = None
        for pkA in sorted(self.pfA.idxtree):
            if len(pkA) > 1: continue
            if pkA[:len(norepeat)] == norepeat: continue
            if len(self.equivalences[pkA])==0:
                if len(pkA) > 1:
                    if prevprint is None: continue
                    else:
                        if len(pkA) > len(prevprint) and prevprint[:-1] == pkA[:len(prevprint)-1]: continue
                        elif pkA < len(prevprint): prevprint = None
                        elif prevprint[:-1] != pkA[:len(prevprint)-1]: prevprint = None

            print pkA,":",

            for pkB, punt in self.equivalences[pkA].iteritems():
                if punt > 0.96:
                    norepeat = pkA
                if punt >= 0.1:
                    print pkB, punt, ";",
                    prevprint = pkA
            print
        """
        """
            for pkB, punt in self.equivalences[pkA].iteritems():
                if punt > 0.96:
                    norepeat = pkA
                    print ">>", ".".join(["%02d" % x for x in pkB])
                    prevprint = pkA
            """



    def getMaxKnown(self,pkA):
        pkA = tuple(pkA)
        if len(pkA) == 0: return 1.0, None
        if pkA not in self.max_known_eq: return 0.0, None
        pkB = self.max_known_eq[pkA]
        eq_prob = self.equivalences[pkA][pkB]
        return eq_prob, pkB


    def addEquivalences(self,lpkA,lpkB):
        lstEquivalences = self.multiplyEquivalences(lpkA,lpkB)
        base_probability = old_div(1.0, len(lstEquivalences))
        if base_probability < 0.01: return

        for pkA,pkB in lstEquivalences:
            probability = base_probability
            parentA = pkA[:-1]
            parent_prob, parentB = self.getMaxKnown(parentA)
            if parentB:
                if parentB != pkB[:-1]: parent_prob = old_div((1-parent_prob), 2.0)
                probability *= parent_prob

            parentB = pkB[:-1]
            if probability < 0.01: continue
            if pkA not in self.equivalences:
                self.equivalences[pkA] = {}
            if pkB in self.equivalences[pkA]:
                print("DUPLICATE", pkA,pkB)
            self.equivalences[pkA][pkB] = probability
            previousMax, prevPkB = self.getMaxKnown(pkA)
            if probability > previousMax:
                self.max_known_eq[pkA] = pkB



    def multiplyEquivalences(self,lpkA,lpkB):
        leq = set([])
        for pkA in lpkA:
            for pkB in lpkB:
                leq|=set([(pkA,pkB)])
        return list(leq)


def process(filename):
    table, idxdepth,idxtree = load(filename)
    #print table.items()[:10]
    treebydepth = {}

    for k in sorted(idxtree.keys()):
        td = len(k)-1
        if td not in treebydepth: treebydepth[td] = []
        treebydepth[td].append(k)
    nitems = 0
    maxitems = 0
    maxd = 0
    hashes = {}
    list_hashes = []

    for d,idx in treebydepth.items():
        if d > 2: break
        nitems = len(idx)
        if maxitems < nitems: maxitems = nitems
        elif nitems * 2 < maxitems: break
        #print "Depth:", d, "(%d items)" % nitems
        maxd = d
        for k in idx:
            #print ".".join([str(x) for x in k])
            pk = idxtree[k]
            r = table[pk]
            rhash = r["hash"]
            if rhash not in hashes:
                list_hashes.append(rhash)
                hashes[rhash] = []
            hashes[rhash].append(k)
    return table, idxdepth,idxtree, hashes, list_hashes

def isinside(parent, child):
    pfrom, pto = parent
    cfrom, cto = child
    pto += 1
    if cfrom >= pfrom and cto <= pto: return 0
    if cfrom < pfrom and cto < pfrom: return -1
    if cfrom > pto and cto > pto: return 1
    #print "ERROR:", child , " is superior to ", parent
    return 0

def load(filename):
    file = open(filename)
    def getpk(row):
        return (row["start"],row["end"])

    fields = [
        "depth",
        "hash",
        "start",
        "end",
        "name",
        "len"
        ]
    rows = {}
    intfields = [
        "depth",
        "start",
        "end",
        "len"
        ]
    bydepth = {}
    for line in file:
        row = dict(list(zip(fields,line[:-1].split("\t"))))
        for f in intfields: row[f]=int(row[f])
        pk = getpk(row)
        depth = row["depth"]
        if depth not in bydepth: bydepth[depth] = []
        bydepth[depth].append(pk)
        rows[pk]=row

    for dpth, items in bydepth.items():
        bydepth[dpth] = list(sorted(items))

    idxtree = {}
    for currdepth in bydepth:
        n = 0
        #print "Depth:", currdepth
        if currdepth == 0:
            nparent = []
        else:
            pdepth = currdepth - 1
            np = 0

        for pk in bydepth[currdepth]:
            n+=1
            if currdepth > 0:
                offset = 99
                it = 0
                while offset != 0:
                    it += 1
                    assert(np >=0)
                    assert(np <len(bydepth[pdepth]))
                    ppk = bydepth[pdepth][np]
                    offset = isinside(ppk,pk)
                    np += offset
                    if offset: n = 1
                    if offset < 0:
                        print(list(enumerate(bydepth[pdepth])))
                        assert(offset >= 0)
                    #if it > 100:
                    #    print it,n,pk,np, ppk, offset
                    #    if offset < 0:
                    #        print list(enumerate(bydepth[pdepth]))
                    #        assert(offset >= 0)
                    #    assert(it < 250)

                prow = rows[ppk]
                nparent = prow["tree_id"]


            row = rows[pk]
            tree_id = nparent + [n]
            row["tree_id"] = tree_id
            if tuple(tree_id) in idxtree:
                print("ERROR:", tuple(tree_id), " is duplicated:")
                print("previous:", idxtree[tuple(tree_id)])
                print("new:" , pk)
            else:
                idxtree[tuple(tree_id)] = pk




    return rows, bydepth, idxtree


if __name__ == "__main__": main()
