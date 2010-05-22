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
            pf.table, pf.idxdepth,pf.idxtree, pf.hashes, pf.list_hashes = process(file1)
            pfiles.append(pf)
        basehashes = pfiles[0].list_hashes
        for pf in pfiles[1:]:
            for key in basehashes:
                if key not in pf.hashes:
                    print "Lost:", pfiles[0].hashes[key] , "==>", "???"
                else:
                    print "Found:", pfiles[0].hashes[key] , "==>", pf.hashes[key]

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
        elif nitems < maxitems: break
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
                    if it > 10:
                        print it,n,pk,np, ppk, offset
                        if offset < 0:
                            print list(enumerate(bydepth[pdepth]))
                            assert(offset >= 0)
                        assert(it < 25)
                
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