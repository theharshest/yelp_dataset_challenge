# -*- coding: utf-8 -*-
"""
Generate a dataset using data that was available prior to a specified prediction
date.

Arguments:
  pdate    - the prediction date to use for generating the data set
  busjson  - path to the file where filtered business data should be written
  revjson  - path to the file where filtered review data should be written
  tipjson  - path to the file where filtered tip data should be written
  outfile  - path to the file where the generated data set should be written

Created on Wed Dec  3 23:00:59 2014

@author: John Maloney
"""

import jsonutils as ju
import datautils as du
import sys

def main():
    if (len(sys.argv) < 5):
        usage(sys.argv)
        return

    pdate   = sys.argv[1]
    busjson = sys.argv[2]
    revjson = sys.argv[3]
    tipjson = sys.argv[4]
    outfile = sys.argv[5]

    run_script(pdate, busjson, revjson, tipjson, outfile)
# end main

def run_script(pdate_str, busjson, revjson, tipjson, outfile):
    # convert pdate to seconds since the epoch
    pdate = du.date2int(du.str2date(pdate_str))

    # load business objects
    print 'Loading business objects from %s...' % busjson
    all_buses, junk = ju.load_objects(busjson)

    # load review objects
    print 'loading review objects from %s...' % revjson
    all_reviews, junk = ju.load_objects(revjson)

    # load tip objects
    print 'loading tip objects from %s...' % tipjson
    all_tips, junk = ju.load_objects(tipjson)
    
    # generate a data set the specified prediction date
    print('generate data set for prediction date %s...' % pdate_str)
    buses = du.gen_dataset(pdate, all_buses, all_reviews, all_tips)
    
    # write data set to file
    print('writing generated data set to %s...' % outfile)
    ju.save_objects(buses, outfile)
# end run_script

def usage(argv):
    print 'Usage: %s <pdate> <busjson> <revjson> <tipjson> <outfile>' % argv[0]
# end usage

# run main method when this file is run from command line
if __name__ == "__main__":
    main()