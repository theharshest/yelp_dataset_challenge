# -*- coding: utf-8 -*-
"""
Generate a dataset using data that was available prior to a specified prediction
date.

Arguments:
  pdate    - the prediction date to use for generating the data set
  busjson  - path to the file where filtered business data is stored
  revjson  - path to the file where filtered review data is stored
  tipjson  - path to the file where filtered tip data is stored
  outfile  - path to the file where the generated data set should be written

Created on Wed Dec  3 23:00:59 2014

@author: John Maloney
"""

import jsonutils as ju
import csvutils as cu
import datautils as du
import argparse

def main():
    desc = 'Generate a dataset using data that was available prior to a specified prediction date'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('pdate', help='the prediction date to use for generating the data set')
    parser.add_argument('busjson', help='path to the file where filtered business data is stored')
    parser.add_argument('revjson', help='path to the file where filtered review data is stored')
    parser.add_argument('tipjson', help='path to the file where filtered tip data is stored')
    parser.add_argument('senticsv', help='path to the file where sentiment rank data is stored')
    parser.add_argument('outfile', help='path to the file where the generated data set should be written')

    args = parser.parse_args()

    run_script(args.pdate, args.busjson, args.revjson, args.tipjson, args.senticsv, args.outfile)
# end main

def run_script(pdate_str, busjson, revjson, tipjson, senticsv, outfile):
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
    
    # load sentiment ranking data derived from tip and review data
    print 'loading sentiment rankings from %s...' % senticsv
    all_senti = cu.load_matrix(senticsv, has_hdr=False)

    # generate a data set the specified prediction date
    print('generate data set for prediction date %s...' % pdate_str)
    buses = du.gen_dataset(pdate, all_buses, all_reviews, all_tips, all_senti)
    
    # write data set to file
    print('writing generated data set to %s...' % outfile)
    ju.save_objects(buses, outfile)
# end run_script

# run main method when this file is run from command line
if __name__ == "__main__":
    main()