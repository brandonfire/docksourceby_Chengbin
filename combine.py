#!/bin/env python
"""Combine dock output and check for excess zeroes.

usage: combine.py

Output:
combine.scores - Final combined scores
combine.zeroes - Number of zeroes found in each scoring column of combine.scores
         <# unique ids> <shape> <elec> <vdw> <psolv> <asolv> <total>
combine.broken - Summary of broken molecules
combine.raw - The raw combined OUTDOCK scores, before any processing

Michael Mysinger 200707 Created
Michael Mysinger 200801 Update for broken filters
Michael Mysinger 200802 Account for docked but unscored molecules
Michael Mysinger 201001 Use minimal memory plus unix sort command
"""

import os
import sys
import itertools
import subprocess
from optparse import OptionParser
import mmmutils
import broken
import check
from progressbar import ProgressBar

# Output files
BROKEN = "combine.broken"
SCORES = "combine.scores"
ZEROES = "combine.zeroes"

# Temporary files
RAW = "combine.raw"
EXTRAS = "combine.extras"
SORTED = "combine.sorted"
CATTED = "combine.catted"

OUTPUT_PREFIX="test"
SENTINEL = "COMBINED"

SORT_CMD = ["sort", "-n", "--key=7,7"]
CAT_CMD = ["cat"]
UNIQUE_CMD = ["awk", "!($1 in a) {a[$1]; print}"]

def number_of_lines(filename):
    """Compute number of lines in filename."""
    f = open(filename)
    nlines = sum(1 for x in f)
    f.close()
    return nlines

def launch(command, filename): 
    """Lauch subprocess command, writing stdout to filename."""
    outf = open(filename, 'w')
    sp = subprocess.Popen(command, stdout=outf)
    sp.communicate()
    outf.close()

def check_zeroes(scores):
    """Compute number of zeroes in each column of scores."""
    first = scores.next()
    zeroes = [0 for x in first[:-1]]
    for line in itertools.chain([first], scores):
        zeroes[0] += 1
        for i, x in enumerate(line[1:-1]):
            if x == '0.00':
                zeroes[i+1] += 1
    return zeroes

def read_scores(subdir, extrasf):
    outdock = os.path.join(subdir, 'OUTDOCK')
    extra = None
    for line in mmmutils.flex_open(outdock):
        spl = line.split()
        if (len(spl) > 6 and spl[0].isdigit() and 
            line[25:35].strip().isdigit() and '.' in spl[-2]):
            if extra is not None:
                extrasf.write(extra+"\n")
            extra = spl[1]
        elif len(spl) == 8 and ' E ' in line:
            yield spl[1:] + [subdir]
            if extra is None:
                raise ValueError("Fatal parsing mismatch in %s!\n" % 
                                 outdock + "Line: %s!" % line)
            else:
                extra = None
    if extra is not None:
        extrasf.write(extra+"\n")

def combine_dirs(indir, rawf, extrasf, brokensf, 
                 box=broken.BOX_FILE, prefix=OUTPUT_PREFIX):
    """Combine scores and parse .eel1s for all subdirs."""
    sys.stdout.write("\nProcessing subdirs: ")
    subdirs = list(mmmutils.read_dirlist(indir))
    pb = ProgressBar(len(subdirs))
    nbroken = 0
    for subdir in subdirs:
        pb.progress()
        scores = read_scores(subdir, extrasf)
        eel1fn = os.path.join(subdir, prefix+'.eel1.gz')
        if brokensf is not None and os.path.exists(eel1fn):
            eel1f = mmmutils.flex_open(eel1fn)
            boxf = open(os.path.join(subdir, box), 'r')
            brokens = dict(broken.get_broken(eel1f, boxf))
            eel1f.close()
            boxf.close()
            for k in brokens:
                id, sc = k.split(':')
                brokensf.write("%s;%s;%s;%s\n" %
                               (id, sc, subdir, brokens[k]))
                extrasf.write("%s\n" % k.split(':')[0])
            scores = (x for x in scores if x[0]+':'+x[6] not in brokens)
            nbroken += len(brokens)
        mmmutils.write_splits(rawf, scores, raw_file=True)
    sys.stdout.write("\n")
    return nbroken

def process_subdirs(indir='.', outdir=None, box=broken.BOX_FILE, 
                    prefix=OUTPUT_PREFIX, checkdone=True, checkbroken=False):
    """Combine dock output, remove brokens, and keep uniques."""

    if outdir is None:
        outdir = indir
    # extras serves as a lock file indicating combine is running here
    extrasfn = os.path.join(outdir, EXTRAS)
    if os.path.exists(os.path.join(outdir, SCORES)):
        print "Not running because", SCORES, "file already exists." 
        print "Delete", SCORES, "file and re-run if needed."
        return None

    if os.path.exists(extrasfn):
            print "Error! Another combine is running in this directory!"
            print "  If no other combine is running, remove %s" % extrasfn
            return None        
    if checkdone:
        if not check.docheck(indir=indir):
            print "Error! The above jobs are not done, use --done to override!"
            return None

    sys.stdout.write("Starting combine phase!\n")
    sys.stdout.write("Input directory: %s\n" % indir)
    sys.stdout.write("Output directory: %s\n" % outdir)
    sys.stdout.write("Relative box location: %s\n" % box)
    sys.stdout.write("Dock structure file prefix: %s\n" % prefix)
    rawfn = os.path.join(outdir, RAW)
    brokensfn = os.path.join(outdir, BROKEN)
    rawf = open(rawfn, 'w')
    extrasf = open(extrasfn, 'w')
    try:
        if checkbroken:
            brokensf = open(brokensfn, 'w')
        else:
            brokensf = None
        nbroken = combine_dirs(indir, rawf, extrasf, brokensf,
                               box=box, prefix=prefix)
        rawf.close()
        extrasf.close()
        if brokensf is not None:
            brokensf.close()

        print "%d out of bounds or broken molecules found" % nbroken
        nextra = number_of_lines(extrasfn)
        nextra -= nbroken
        print ( "%d non-scored molecules (bumped, no_matched, etc.) found" % 
                nextra )
        # display more statistics??? 

        sortedfn = os.path.join(outdir, SORTED)
        launch(SORT_CMD+[rawfn], sortedfn)
        os.remove(rawfn)

        cattedfn = os.path.join(outdir, CATTED)
        launch(CAT_CMD+[sortedfn, extrasfn], cattedfn)
        os.remove(sortedfn)

        uniqfn = os.path.join(outdir, SCORES)
        launch(UNIQUE_CMD+[cattedfn], uniqfn)
        os.remove(cattedfn)

        scores = mmmutils.read_splits(uniqfn)
        zeroes = check_zeroes(scores)
        zeroes = [str(x) for x in zeroes]
        mmmutils.write_splits(os.path.join(outdir, ZEROES), [zeroes])
        print "zeroes in score columns:", ' '.join(zeroes)

        # add finishing sentinel to scores file
        uniqf = open(uniqfn, 'a')
        uniqf.write(SENTINEL+"\n")
        uniqf.close()
        return True

    finally:
        # remove lock file
        os.remove(extrasfn)

def main(argv):
    description = "Combine dock output, remove brokens, and keep uniques."
    usage = "%prog [options]"
    version = "%prog *version 201001* created by Michael Mysinger"
    parser = OptionParser(usage=usage, description=description,
                          version=version)
    parser.set_defaults(indir='.', outdir=None, box=broken.BOX_FILE, 
                        prefix=OUTPUT_PREFIX, done=True, broken=False)
    parser.add_option("-i", "--indir",
           help="input directory (default: %default)")  
    parser.add_option("-o", "--outdir",
           help="output directory (default: --indir)")
    parser.add_option("-p", "--prefix", 
           help="output file prefix (default: %default)")
    parser.add_option("--box", help= ("box file location relative to " +
           "OUTDOCK sub-directories (default: %default)") )
    parser.add_option("-d", "--done", action="store_false",
           help="remove checks to determine that docking is done")  
    parser.add_option("-b", "--broken", action="store_false",
           help="skip finding broken molecules (now default)")  
    parser.add_option("-e", "--enable-broken", action="store_true", 
                      dest="broken", 
                      help="enable finding broken molecules")  
    options, args = parser.parse_args(args=argv[1:])
    if len(args):
        parser.error("program takes no positional arguments.\n" +
                     "  Use --help for more information.")
    results = process_subdirs(indir=options.indir, outdir=options.outdir, 
                  box=options.box, prefix=options.prefix, 
                  checkdone=options.done, checkbroken=options.broken)
    return not results

if __name__ == '__main__':
    sys.exit(main(sys.argv))
