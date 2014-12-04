# -*- coding: utf-8 -*-
"""
Generate a dataset using data that was available prior to a specified prediction
date.

Arguments:
  jsonfile  - path to the JSON file (input)
  csvfile   - path to the CSV file (output)

Created on Thu Dec  4 01:07:50 2014

@author: John Maloney
"""

import jsonutils as ju
import csvutils as cu
import sys

def main():
    if (len(sys.argv) < 3):
        usage(sys.argv)
        return

    jsonfile = sys.argv[1]
    csvfile  = sys.argv[2]

    run_script(jsonfile, csvfile)
# end main

def run_script(jsonfile, csvfile):
    # load json objects
    print 'Loading JSON objects from %s...' % jsonfile
    objects, columns = ju.load_objects(jsonfile)

    # write json object to csv file
    print('writing JSON objects to %s...' % csvfile)
    cu.write_objects(csvfile, objects, columns)
# end run_script

def usage(argv):
    print 'Usage: %s <jsonfile> <csvfile>' % argv[0]
# end usage

# run main method when this file is run from command line
if __name__ == "__main__":
    main()