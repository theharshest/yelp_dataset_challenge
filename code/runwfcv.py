# -*- coding: utf-8 -*-
"""
Script used to run "walk forward cross validation".

Arguments:
  busjson  - path to the file where filtered business data should be written
  revjson  - path to the file where filtered review data should be written
  tipjson  - path to the file where filtered tip data should be written
  pdate    - the initial prediction date to use for walking forward
  delta    - the number of months between training prediction date and test
             prediction date (the size of the steps)

Created on Sun Nov 30 23:26:13 2014

@author: John Maloney
"""

import jsonutils as ju
import datautils as du
import feat_info as fi # for class_names
import numpy as np
import wfcvutils
import sklearn.svm as svm
import sklearn.metrics as metrics
import sys

def main():
    if (len(sys.argv) < 6):
        usage(sys.argv)
        return

    busjson    = sys.argv[1]
    revjson    = sys.argv[2]
    tipjson    = sys.argv[3]
    init_pdate = sys.argv[4]
    delta      = int(sys.argv[5])

    run_script(busjson, revjson, tipjson, init_pdate, delta)
# end main

def run_script(busjson, revjson, tipjson, init_pdate, delta):
    print 'Initial prediction date: %s' % init_pdate
    print 'Time delta: %d months' % delta

    # convert pdate to secondds since the epoch
    pdate = du.date2int(du.str2date(init_pdate))

    # load business objects
    print 'Loading business objects from %s...' % busjson
    all_buses, junk = ju.load_objects(busjson)

    # load review objects
    print 'loading review objects from %s...' % revjson
    all_reviews, junk = ju.load_objects(revjson)

    # load tip objects
    print 'loading tip objects from %s...' % tipjson
    all_tips, junk = ju.load_objects(tipjson)
    
    # create classifier to test
    c = svm.LinearSVC()

    # configure parameter grid for grid search
    param_grid = {'C': [1, 10, 100, 1000]}

    # run the walk-forward cross validation and collect the results
    print('run walk-forward cross validation...')
    results = wfcvutils.wfcv(c, param_grid, all_buses, all_reviews, all_tips,
                             pdate, delta*du.month)
    
    # combine the results to produce overall metrics
    y_true = None
    y_pred = None
    for r in results:
        if (y_true is None):
            y_true = r[0]
        else:
            y_true = np.hstack((y_true, r[0]))
        if (y_pred is None):
            y_pred = r[1]
        else:
            y_pred = np.hstack((y_pred, r[1]))
    
    # print out an overall classification report
    print('\nOverall metrics for all prediction dates:\n')
    print(metrics.classification_report(y_true, y_pred, target_names=fi.class_names))
# end run_script

def usage(argv):
    print 'Usage: %s <busjson> <revjson> <tipjson> <pdate> <delta>' % argv[0]
# end usage

# run main method when this file is run from command line
if __name__ == "__main__":
    main()