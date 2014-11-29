# -*- coding: utf-8 -*-
"""
Script used to create the csv data files.

Arguments:
  json_file  - path to the file holding the json data
  data_feats - path to the file holding the list of data features
  data_csv   - path to the location where the data features should be written
  meta_csv   - path to the location where the meta features should be written
  rev_csv    - path to the location where the review features should be written
  tip_csv    - path to the location where the tip features should be written

Created on Mon Nov 03 00:06:14 2014

@author: John Maloney
"""

import feat_info
import datautils
import sys

def main():
    if (len(sys.argv) < 10):
        usage(sys.argv)
        return

    jsonbusfile  = sys.argv[1]
    jsonrevfile  = sys.argv[2]
    jsontipfile  = sys.argv[3]
    csvtractfile = sys.argv[4]
    datafeats    = sys.argv[5]
    datacsv      = sys.argv[6]
    metacsv      = sys.argv[7]
    revcsv       = sys.argv[8]
    tipcsv       = sys.argv[9]
    
    run_script(jsonbusfile, jsonrevfile, jsontipfile, csvtractfile, datafeats, datacsv, metacsv, revcsv, tipcsv)
# end main

def run_script(jsonbusfile, jsonrevfile, jsontipfile, csvtractfile, datafeats, datacsv, metacsv, revcsv, tipcsv):
    print('initializing feature lists')
    feat_info.init_data_feats(datafeats)
    
    print('creating csv files')
    datautils.convert_restaurant_json_to_csv(jsonbusfile, jsonrevfile, jsontipfile, csvtractfile, datacsv, metacsv, revcsv, tipcsv)
# end run_script

def usage(argv):
    print 'Usage: %s <jsonbusfile> <jsonrevfile> <jsontipfile> <csvtractfile> <datafeats> <datacsv> <metacsv> <revcsv> <tipcsv>' % argv[0]
# end usage

# run main method when this file is run from command line
if __name__ == "__main__":
    main()