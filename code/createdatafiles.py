# -*- coding: utf-8 -*-
"""
Script used to create the csv data files.

Arguments:
  in_busjson   - path to the file holding unfiltered yelp business data
  out_busjson  - path to the file where filtered business data should be written
  in_revjson   - path to the file holding unfiltered yelp review data
  out_revjson  - path to the file where filtered review data should be written
  in_tipjson   - path to the file holding unfiltered yelp tip data
  out_tipjson  - path to the file where filtered tip data should be written
  in_censuscsv - path to the file holding census tract mappings for businesses

Created on Mon Nov 03 00:06:14 2014

@author: John Maloney
"""

#import feat_info
import datautils
import sys

def main():
    if (len(sys.argv) < 8):
        usage(sys.argv)
        return

    in_busjson   = sys.argv[1]
    out_busjson  = sys.argv[2]
    in_revjson   = sys.argv[3]
    out_revjson  = sys.argv[4]
    in_tipjson   = sys.argv[5]
    out_tipjson  = sys.argv[6]
    in_censuscsv = sys.argv[7]

    run_script(in_busjson, out_busjson, in_revjson, out_revjson,
               in_tipjson, out_tipjson, in_censuscsv)
# end main

def run_script(in_busjson, out_busjson, in_revjson, out_revjson,
               in_tipjson, out_tipjson, in_censuscsv):
    #print('initializing feature lists')
    #feat_info.init_data_feats(datafeats)
    
    print('creating filtered JSON files...')
    datautils.filter_yelp_data(in_busjson, out_busjson, in_revjson, out_revjson,
                               in_tipjson, out_tipjson, in_censuscsv)
# end run_script

def usage(argv):
    print 'Usage: %s <in_busjson> <out_busjson> <in_revjson> <out_revjson> <in_tipjson> <out_tipjson> <in_censuscsv>' % argv[0]
# end usage

# run main method when this file is run from command line
if __name__ == "__main__":
    main()