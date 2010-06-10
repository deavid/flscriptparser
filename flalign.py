import os, os.path, sys
import math
from optparse import OptionParser
import difflib 
import re

class ProcessFile:
    def __init__(self, filename):
        self.filename = filename
        self.process()
        self.bnames = set(self.idxnames.keys())

    def process(self):
        self.blocks = []
        self.idxlines = {}
        self.idxnames = {}
        
        fblocks = open(self.filename + ".blocks")
        n = 0
        line = fblocks.readline()
        while line:
            start, end, name = line.strip().split("\t")
            self.blocks.append( (start,end, name) )
            self.idxlines[start] = n
            if name in self.idxnames:
                self.idxnames[name] = None
            else:
                self.idxnames[name] = n
            n+=1
            line = fblocks.readline()
    
    def diffTo(self,pfile2):
        added = pfile2.bnames - self.bnames
        deleted = self.bnames - pfile2.bnames
        
        return added, deleted
        
        
def appliedDiff(ptarget, pfrom, pto):
    added, deleted = pfrom.diffTo(pto)
    plist = []
    for start,end,name in ptarget.blocks:
        if name in added:
            n = pto.idxnames[name]
            start,end,name = pto.blocks[n]
            bobject = pto.filename
        elif name in deleted:
            continue
        else:
            bobject = ptarget.filename
            plist.append((bobject,start,end,name))
    
    return plist

def main():
    parser = OptionParser()
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
        return

    if len(filenames) != 3:
        print "MUST have exactly 3 files to align."
    pfiles = []        
    for file1 in filenames:
        print "Load File:", file1
        pf = ProcessFile(file1)
        pfiles.append(pf)

    A = pfiles[0]
    B = pfiles[1]
    C = pfiles[2]
           
    #addedAB, deletedAB = A.diffTo(B)
    #addedAC, deletedAC = A.diffTo(C)
    
    patchlist = appliedDiff(
            ptarget = B,
            pfrom = A,
            pto = C
            )
            
    for elem in patchlist:
        print elem
        
        
if __name__ == "__main__": main()        