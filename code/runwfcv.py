# -*- coding: utf-8 -*-
"""
Script used to run "walk forward cross validation".

Arguments:
  busjson  - path to the file where filtered business data is stored
  revjson  - path to the file where filtered review data is stored
  tipjson  - path to the file where filtered tip data is stored
  pdate    - the initial prediction date to use for walking forward
  delta    - the number of months between training prediction date and test
             prediction date (the size of the steps)

Created on Sun Nov 30 23:26:13 2014

@author: John Maloney
"""

import jsonutils as ju
import datautils as du
import numpy as np
import wfcvutils
import sklearn.svm as svm
import sklearn.metrics as metrics
import sklearn.feature_selection as fs
import argparse

def main():
    desc = 'Run walk-forward cross-validation using the specified initial prediction date and delta'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('busjson', help='path to the file where filtered business data is stored')
    parser.add_argument('revjson', help='path to the file where filtered review data is stored')
    parser.add_argument('tipjson', help='path to the file where filtered tip data is stored')
    parser.add_argument('pdate', help='the initial prediction date to use for walking forward')
    parser.add_argument('delta', type=int, help='the number of months between training prediction ' +
                                                'date and test prediction date (the size of the steps)')
    parser.add_argument('-nus', help='this flag turns off under-sampling for the still open class',
                        action='store_true')
    parser.add_argument('-rbf', help='this flag causes an RBF SVM to be used instead of a linear SVM',
                        action='store_true')
    parser.add_argument('-rfe', help='this flag causes recursive feature elimination to be used',
                        action='store_true')
    parser.add_argument('-pca', type=int, default=-1,
                                help='if present, PCA will be used to reduce the number of features, ' +
                                     'the supplied value indicates how many components to keep, if zero '+
                                     'is supplied then the number of features will not be reduced, if ' +
                                     'a negative value is supplied then PCA is not performed')

    args = parser.parse_args()

    run_script(args.busjson, args.revjson, args.tipjson, args.pdate, args.delta,
               usamp=(not args.nus), rbf=args.rbf, rfe=args.rfe, pca=args.pca)
# end main

def run_script(busjson, revjson, tipjson, init_pdate, delta, usamp=True, rbf=False, rfe=False,pca=-1):
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
    
    # reduce the number of features using recursive feature elimination
    # - See http://scikit-learn.org/stable/auto_examples/plot_rfe_with_cross_validation.html#example-plot-rfe-with-cross-validation-py
    # - See http://stackoverflow.com/questions/23815938/recursive-feature-elimination-and-grid-search-using-scikit-learn

    if (rbf):
        # create RBF SVM to test
        c = svm.NuSVC(kernel='rbf')
        # configure parameter grid for grid search
        if (rfe):
            print 'using RBF SVM with RFE...'
            c = fs.RFECV(c, step=1)
            pgrid = [{'gamma':0.5},{'gamma':0.1},{'gamma':0.01},{'gamma':0.001},{'gamma':0.0001}]
            param_grid = {'estimator_params': pgrid}
        else:
            print 'using RBF SVM...'
            param_grid = {'gamma': [0.5, 0.1, 0.01, 0.001, 0.0001]}
    else:
        # create linear SVM to test
        c = svm.LinearSVC()
        # configure parameter grid for grid search
        if (rfe):
            print 'using linear SVM with RFE...'
            c = fs.RFECV(c, step=1)
            pgrid = [{'C':0.01},{'C':0.1},{'C':1},{'C':10},{'C':100},{'C':1000},{'C':10000}]
            param_grid = {'estimator_params': pgrid}
        else:
            print 'using linear SVM...'
            param_grid = {'C': [0.01, 0.1, 1, 10, 100, 1000, 10000]}

    # run the walk-forward cross validation and collect the results
    print('run walk-forward cross validation...')
    if (usamp):
        print('  under-sampling still open class...')
    else:
        print('  NOT under-sampling still open class...')
    results = wfcvutils.wfcv(c, param_grid, all_buses, all_reviews, all_tips,
                             pdate, delta*du.month, pca=pca, usamp=usamp)
    
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
    print('\n=========================================')
    print('Overall metrics for all prediction dates:\n')
    if (len(results) != 0):
        cm = metrics.confusion_matrix(y_true, y_pred)
        wfcvutils.print_cm(cm)
        #print(metrics.classification_report(y_true, y_pred, target_names=fi.class_names))
    else:
        print '  NO RESULTS\n'
# end run_script

# run main method when this file is run from command line
if __name__ == "__main__":
    main()