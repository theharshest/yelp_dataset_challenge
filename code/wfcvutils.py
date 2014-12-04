# -*- coding: utf-8 -*-
"""
Utilities for doing "walk forward cross validation".

Created on Sun Nov 30 09:51:14 2014

@author: John Maloney
"""

import time
import feat_info as fi
import datautils as du
import jsonutils as ju
import sklearn.metrics as metrics
import sklearn.grid_search as grid_search

'''
Estimate the generalization error rate using the "walk forward cross validation"
approach.

Inputs:

  clf:
    the classifier to be tested

  param_grid:
    dictionary with parameters names (string) as keys and lists of parameter
    settings to try as values, or a list of such dictionaries, in which case
    the grids spanned by each dictionary in the list are explored. This enables
    searching over any sequence of parameter settings

  all_buses:
    all the business objects available for generating train and test datasets

  all_reviews:
    all the review objects available for generating train and test datasets

  all_tips:
    all the tip objects available for generating train and test datasets

  init_pdate:
    the initial prediction date to use (in seconds since the epoch)

  time_delta
    the amount of time between training prediction date and test prediction
    date (in seconds)

Outputs:

  results:
    a list of tuples, one tuple for each round of cross validation, the first
    element in each tuple provides the true values for that round's test examples
    and the second element provides the predictions generated by the classifier
    on that round's test examples
'''
def wfcv(clf, param_grid, all_buses, all_reviews, all_tips, init_pdate, time_delta):
    # find the earliest and latest review dates
    start_date = int(time.time())
    end_date = 0
    for bus in all_buses:
        first_review_date = bus[fi.first_review_date]
        last_review_date = bus[fi.last_review_date]
        if (first_review_date < start_date):
            start_date = first_review_date
        if (last_review_date > end_date):
            end_date = last_review_date
    
    # initialize the "prediction date"
    pdate = init_pdate

    # create variables for the training data - it will be populated later
    X_train,y_train = None,None

    # generate the first data set
    buses_test = du.gen_dataset(pdate, all_buses, all_reviews, all_tips)    
    X_test,y_test = ju.json2xy(buses_test, fi.data_feat_info, fi.label)

    # initialize the stop_date threshold
    stop_date = end_date - 2*time_delta

    # create list to hold results
    results = []

    # perform "walk forward cross validation"
    while (pdate <= stop_date):
        # update the prediction date for the this round
        pdate = pdate + time_delta

        # use current test set as training set for this round
        X_train = X_test
        y_train = y_test

        # generate a new test set for this round
        buses_test = du.gen_dataset(pdate, all_buses, all_reviews, all_tips)    
        X_test,y_test = ju.json2xy(buses_test, fi.data_feat_info, fi.label)

        # use grid search to train and test the classifier:
        # - see http://scikit-learn.org/stable/auto_examples/grid_search_digits.html#example-grid-search-digits-py

        # configure scoring metric to be used during grid search
        # - select a metric that is suited to unbalanced classification
        #scoring_metric = metrics.f1_score

        # train the classifier using grod search
        # start by using deafults
        gs = grid_search.GridSearchCV(clf, param_grid, n_jobs=-1)
        #gs = grid_search.GridSearchCV(clf, param_grid, cv=5, scoring=scoring_metric)
        #                              n_jobs=n_jobs, pre_dispatch=n_jobs)
        gs.fit(X_train, y_train)

        print("\nBest parameters set found on development set:\n")
        print(gs.best_estimator_)
        print("\nGrid scores on development set:\n")
        for params, mean_score, scores in gs.grid_scores_:
            print("%0.3f (+/-%0.03f) for %r"
              % (mean_score, scores.std() / 2, params))

        # collect predictions from the classifier
        y_pred = gs.predict(X_test)

        print("\nScores on evaluation set:\n")
        print(metrics.classification_report(y_test, y_pred, target_names=fi.class_names))

        # save results
        results.append((y_test, y_pred))
    #end while

    # return the true values and predictions for each round
    return results
#end wfocv