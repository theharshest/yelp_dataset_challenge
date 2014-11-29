# -*- coding: utf-8 -*-
"""
Script used to create the restaurant data features file and the restaurant
meta data file.

Arguments:
  json_file  - path to the file holding the json data
  data_feats - path to the file holding the list of data features
  data_csv   - path to the location where the data features should be written
  meta_csv   - path to the location where the meta features should be written

Created on Mon Nov 03 00:06:14 2014

@author: John Maloney
"""

import feat_info
import datautils
import sys

def main():
    if (len(sys.argv) < 8):
        usage(sys.argv)
        return

    jsonbusfile  = sys.argv[1]
    jsonrevfile  = sys.argv[2]
    csvtractfile = sys.argv[3]
    datafeats    = sys.argv[4]
    datacsv      = sys.argv[5]
    metacsv      = sys.argv[6]
    revcsv       = sys.argv[7]
    
    run_script(jsonbusfile, jsonrevfile, csvtractfile, datafeats, datacsv, metacsv, revcsv)
# end main

def run_script(jsonbusfile, jsonrevfile, csvtractfile, datafeats, datacsv, metacsv, revcsv):
    print('initializing data features')
    feat_info.init_data_feats(datafeats)
    
    print('creating data file and meta data file')
    datautils.convert_restaurant_json_to_csv(jsonbusfile, jsonrevfile, csvtractfile, datacsv, metacsv, revcsv)
# end run_script

def usage(argv):
    print 'Usage: %s <jsonbusfile> <jsonrevfile> <csvtractfile> <datafeats> <datacsv> <metacsv> <revcsv>' % argv[0]
# end usage

# run main method when this file is run from command line
if __name__ == "__main__":
    main()