import os, os.path, sys
import math
from optparse import OptionParser

class processedFile:
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

    (options, args) = parser.parse_args()
    if options.optdebug:
        print options, args

    filenames = filter(lambda x: os.path.isfile(x) , args)
    not_a_file = set(args) - set(filenames)
    if len(not_a_file):
        print "WARNING: Not a file:", ", ".join(not_a_file)

    if len(filenames):
        pfiles = []
        for file1 in filenames:
            print "File:", file1
            pf = processedFile()
            pf.filename = file1
            pf.table, pf.idxdepth,pf.idxtree, pf.hashes, pf.list_hashes = process(file1)
            pfiles.append(pf)
        pfA = pfiles[0]
        for pfB in pfiles[1:]:
            feq = FindEquivalences(pfA, pfB)
def tree_parents(pk):
    parents = []
    while (len(pk)>0):
        parents.append(pk)
        pk = pk[:-1]
    return parents

class FindEquivalences:
    def __init__(self,pfA, pfB, autoCompute = True):
        self.equivalences = {}
        self.parent_equivalences = {}
        self.max_known_eq = {}
        self.pfA, self.pfB = pfA, pfB
        if autoCompute: self.compute()
        
    def compute(self):
        print "Finding equivalences between A (%s) -> B (%s):" % (
                self.pfA.filename, 
                self.pfB.filename
                )
    
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
            for pkB, punt in self.equivalences[pkA].iteritems():
                if len(pkA) != len(pkB): continue
                parentsB = tree_parents(pkB)
                parentsAB = zip(parentsA,parentsB)
                for pA, pB in parentsAB:
                    sz2a, sz2b = self.pfA.idxtree[pkA]
                    sz2 = sz2b - sz2a 
                    sz1a, sz1b = self.pfA.idxtree[pA]
                    sz1 = sz1b - sz1a 
                    lev2 = 1.0 + sz1 / float(sz2)
                    #lev2 = 2**(len(pkA) - len(pA))
                    #lev2_list = [ pC for pC in self.pfA.idxtree if len(pC) >= len(pA) and pC[:len(pA)] == pA ]
                    #lev2_plist = set([])
                    #for l in lev2_list:
                    #    lev2_plist |= set(tree_parents(l)[1:])
                    #lev2 = len(set(lev2_list) - set(lev2_plist))
                            
                    pEq = (pB, float(punt)/lev2)
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
                                
            for key, punt in count.copy().iteritems():
                if ppB and key[:-1] != ppB: continue  
                if punt >= 0.01:
                    rcount.append((round(punt*100),key))
                    
            rowA = self.pfA.table[self.pfA.idxtree[pA]]
            if len(rcount):
                punt, pB = max(rcount)
                self.parent_equivalences2[pA] = pB
                rowB = self.pfB.table[self.pfB.idxtree[pB]]
                print "parent:", pA, rowA['name'], "%d%%\t" % punt, pB, len(rcount) , rowB['name']
                if punt > 60:
                    norepeat = pA
            else:        
                print "parent:", pA, rowA['name'], "0%\t  ???"
                
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
        base_probability = 1.0 / len(lstEquivalences)
        if base_probability < 0.01: return

        for pkA,pkB in lstEquivalences:
            probability = base_probability
            parentA = pkA[:-1]
            parent_prob, parentB = self.getMaxKnown(parentA)
            if parentB:
                if parentB != pkB[:-1]: parent_prob = (1-parent_prob) / 2.0
                probability *= parent_prob 
                
            parentB = pkB[:-1]
            if probability < 0.01: continue
            if pkA not in self.equivalences:
                self.equivalences[pkA] = {}
            if pkB in self.equivalences[pkA]:
                print "DUPLICATE", pkA,pkB
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
    
    for d,idx in treebydepth.iteritems():
        nitems = len(idx)
        if maxitems < nitems: maxitems = nitems
        elif nitems * 30 < maxitems: break
        print "Depth:", d, "(%d items)" % nitems
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
        row = dict(zip(fields,line[:-1].split("\t")))
        for f in intfields: row[f]=int(row[f])
        pk = getpk(row)
        depth = row["depth"]
        if depth not in bydepth: bydepth[depth] = []
        bydepth[depth].append(pk)
        rows[pk]=row
        
    for dpth, items in bydepth.iteritems():
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
                    if it > 100:
                        print it,n,pk,np, ppk, offset
                        if offset < 0:
                            print list(enumerate(bydepth[pdepth]))
                            assert(offset >= 0)
                        assert(it < 250)
                
                prow = rows[ppk]
                nparent = prow["tree_id"]
                
                
            row = rows[pk]
            tree_id = nparent + [n]
            row["tree_id"] = tree_id
            if tuple(tree_id) in idxtree:
                print "ERROR:", tuple(tree_id), " is duplicated:"
                print "previous:", idxtree[tuple(tree_id)] 
                print "new:" , pk
            else:
                idxtree[tuple(tree_id)] = pk 
            
            
            
    
    return rows, bydepth, idxtree
    

if __name__ == "__main__": main()