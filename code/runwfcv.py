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
import feat_info as fi
import numpy as np
import wfcvutils
import sklearn.svm as svm
import sklearn.metrics as metrics
import sklearn.feature_selection as fs
import sklearn.tree as tree
import sklearn.ensemble as ensemble
import sklearn.neighbors as neigh
import argparse

# classifier types
linsvm = 'linsvm'
rbfsvm = 'rbfsvm'
ada = 'ada'
knn = 'knn'
rf = 'rf'
dt = 'dt'

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
    parser.add_argument('-rfe', help='this flag causes recursive feature elimination to be used (not '+
                                     'supported for all classifiers)', action='store_true')
    parser.add_argument('-pca', type=int, default=-1,
                                help='if present, PCA will be used to reduce the number of features, ' +
                                     'the supplied value indicates how many components to keep, if zero '+
                                     'is supplied then the number of features will not be reduced, if ' +
                                     'a negative value is supplied then PCA is not performed')
    parser.add_argument('-la', help='if this flag is specified, then the available attributes '+
                                       'are listed and the program exits', action='store_true')

    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('-a', help='the list of attributes to use for classification', nargs='+')
    group1.add_argument('-na', help='the list of attributes NOT to use for classification', nargs='+')

    # supported classifiers
    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('-linsvm', help='use an SVM classifier with a linear kernel',
                        action='store_const', const=linsvm, dest='ctype')
    group2.add_argument('-rbfsvm', help='use an SVM classifier with an RBF kernel',
                        action='store_const', const=rbfsvm, dest='ctype')
    group2.add_argument('-ada', help='use AdaBoost for classification',
                        action='store_const', const=ada, dest='ctype')
    group2.add_argument('-knn', help='use a k-nearest neighbors classifier',
                        action='store_const', const=knn, dest='ctype')
    group2.add_argument('-rf', help='use a random forest classifier',
                        action='store_const', const=rf, dest='ctype')
    group2.add_argument('-dt', help='use a decision tree classifier',
                        action='store_const', const=dt, dest='ctype')

    args = parser.parse_args()

    # list the available attributes
    if (args.la):
        print 'available attributes:'
        for attr in fi.data_feat_names:
            # label is always included
            if (attr != fi.label):
                print '  %s' % attr
        return

    # collect the attributes - if specified
    if (args.a):
        # get feature info for the selected features
        feat_info = {}
        # label is always included
        feat_info[fi.label] = fi.data_feat_info[fi.label]
        for attr in args.a:
            # make sure the attribute is valid
            if (attr in fi.data_feat_info):
                feat_info[attr] = fi.data_feat_info[attr]
            else:
                print '%s is not a valid attribute name' % attr
    else:
        feat_info = fi.data_feat_info.copy()

    # remove user specified attributes - if specified
    if (args.na):
        for attr in args.na:
            feat_info.pop(attr, None)

    # run the script
    run_script(args.busjson, args.revjson, args.tipjson, args.pdate, args.delta,
               ctype=args.ctype, usamp=(not args.nus), rfe=args.rfe, pca=args.pca,
               feat_info=feat_info)
# end main

def run_script(busjson, revjson, tipjson, init_pdate, delta, ctype=linsvm,
               usamp=True, rfe=False, pca=-1, feat_info=fi.data_feat_info):
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

    if (ctype==rbfsvm):
        # create RBF SVM to test
        #c = svm.NuSVC(kernel='rbf')
        c = svm.SVC(kernel='rbf')
        # configure parameter grid for grid search
        C_range = 10.0 ** np.arange(-3, 5)
        gamma_range = 10.0 ** np.arange(-4, 3)
        if (rfe):
            print 'RFE not currently supported for RBF SVM...'
            #c = fs.RFECV(c, step=1)
            #pgrid = []
            #for C in C_range:
            #    for gamma in gamma_range:
            #        pgrid.append({'C':C,'gamma':gamma})
            #pgrid = [{'gamma':0.5},{'gamma':0.1},{'gamma':0.01},{'gamma':0.001},{'gamma':0.0001}]
            #param_grid = {'estimator_params': pgrid}
        print 'using RBF SVM...'
        param_grid = dict(gamma=gamma_range, C=C_range)
    elif (ctype==knn):
        # create a KNN classifier
        c = neigh.KNeighborsClassifier()
        if (rfe):
            print 'RFE not currently supported for k-nearesrt neighbors...'
        print 'using k-mearest neighbors...'
        param_grid = {'n_neighbors':[1,2,3,4,5,6,7,8,9,10,15,20,25,30],
                      'weights':['uniform','distance'],
                      'p':[1,2,3,4,5,6,7,8,9,10]}
    elif (ctype==ada):
        # create boosted classifier
        c = ensemble.AdaBoostClassifier()
        if (rfe):
            print 'RFE not currently supported for AdaBoost...'
        print 'using AdaBoost...'
        param_grid = {'n_estimators':[5, 10, 25, 40, 50, 60, 75, 85, 100],
                      'learning_rate':[0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]}
    elif (ctype==rf):
        # create random forest classifier
        c = ensemble.RandomForestClassifier()
        if (rfe):
            print 'RFE not currently supported for random forest...'
        print 'using random forest...'
        param_grid = {'n_estimators':[5, 10, 25, 40, 50, 60, 75, 85, 100],
                      'max_depth':[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, None]}
    elif (ctype==dt):
        # create decision tree classifier
        c = tree.DecisionTreeClassifier()
        # max feats - subtract 1 because data feats includes the class label
        if (rfe):
            print 'RFE not supported with decision trees...'
        print 'using decision tree...'
        param_grid = {'max_depth': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, None]}
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
                             pdate, delta*du.month, pca=pca, usamp=usamp,
                             feat_info=feat_info)
    
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