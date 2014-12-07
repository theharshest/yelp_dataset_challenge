# -*- coding: utf-8 -*-
"""
This modules provides utility functions for working with the Yelp! academic
dataset data files.

Created on Wed Oct 29 18:31:04 2014

@author John Maloney
"""

import json
import feat_info as fi
import time
import math
import jsonutils
import csvutils
import numpy as np

# initialize time constants assuming 30 day months
# - 30 days x 24 hrs/day x 60 min/hr x 60 sec/min
month = 30*24*60*60
year = 12*month

'''
Generate data sets that contain values that were available on the specified
prediction dates.  Each generated dataset will be written to the file:

   <outdir>/<pdate>.json

Inputs:

  pdates:
    a list of prediction dates to use for generating the datasets (each date is
    a string formatted as YYYY-MM-DD)

  busjson:
    the path to the file containing all the JSON business objects

  revjson:
    the path to the file containing all the JSON review objects

  tipjson:
    the path to the file containing all the JSON tip objects

  outdir:
    the path to the directory where the resulting datasets should be written
'''
def gen_dataset_files(pdates, busjson, revjson, tipjson, outdir):
    # load business objects
    print 'Loading business objects from %s...' % busjson
    all_buses, junk = jsonutils.load_objects(busjson)

    # load review objects
    print 'loading review objects from %s...' % revjson
    all_reviews, junk = jsonutils.load_objects(revjson)

    # load tip objects
    print 'loading tip objects from %s...' % tipjson
    all_tips, junk = jsonutils.load_objects(tipjson)

    # generate the datsets
    for pdatestr in pdates:
        # convert prediction date to int (seconds since epoch)
        pdate = date2int(str2date(pdatestr))

        # generate the dataset for the specified prediction date
        print 'generating dataset for prediction date %s (%d)...' % (pdatestr,pdate)
        buses = gen_dataset(pdate, all_buses, all_reviews, all_tips)

        # generate filename for dataset
        outfile = outdir + '/' + pdatestr + '.json'

        # write dataset to file
        print 'writing %d JSON objects to %s...' % (len(buses),outfile)
        jsonutils.save_objects(buses, outfile)
    # end for
# end gen_dataset_file

'''
Generate a data set that contains values that were available on the specified
prediction date.

Inputs:

  pdate:
    the prediction date to use for generating the dataset (an int expressed as
    seconds since the epoch)

  all_buses:
    all the JSON business objects to consider for the dataset

  all_reviews:
    all the JSON review objects to consider for the dataset

  all_tips:
    all the JSON tip objects to consider for the dataset

  verbose: (optional)
    flag indicating whether verbose output should be produced (default is False)

  usamp: (optional)
    flag indicating whether the "stil open" class should be undersampled so that
    the proportion of samples in this class is similar to the proportion of
    samples in the other classes (default is True)

Outputs:

  buses:
    the JSON business objects selected for the dataset augmented with review
    and tip data (and eventually with census and economic data), a copy is made
    of the original JSON objects so that the objects in all_buses are not modified
'''
def gen_dataset(pdate, all_buses, all_reviews, all_tips, verbose=False, usamp=True):
    pdate_plus_3mos  =  pdate+3*month # end of following year 1st quarter
    pdate_plus_6mos  =  pdate+6*month # end of following year 2nd quarter
    pdate_plus_9mos  =  pdate+9*month # end of following year 3rd quarter
    pdate_plus_12mos = pdate+12*month # end of following year 4th quarter

    # filter businesses that were not open before pdate or closed before pdate
    # and set the class label for those that remain
    buses = {}
    class_counts = [0, 0, 0, 0, 0]
    for orig_bus in all_buses:
        open_date = orig_bus.get(fi.first_review_date,None)
        is_open = orig_bus[fi.is_open]
        close_date = orig_bus.get(fi.close_date,None)
        # make sure the restaurant meets the folowing criteria:
        # - opened on or before the prediction date
        # - is still open or closed after the prediction date
        if ( ((open_date is not None) and (open_date <= pdate)) and
             (is_open or ((close_date is not None) and (close_date > pdate))) ):
            # business meets the criteria - add a copy to dictionary
            bus = orig_bus.copy()
            buses[bus[fi.business_id]]=bus
            # set class label for business
            if (is_open or (close_date > pdate_plus_12mos)):
                # still open 12 months after pdate
                bus[fi.label] = fi.still_open
                class_counts[fi.still_open] = class_counts[fi.still_open] + 1
            if ((close_date > pdate) and (close_date <= pdate_plus_3mos)):
                # closed 0-3 months after pdate
                bus[fi.label] = fi.closed_q1
                class_counts[fi.closed_q1] = class_counts[fi.closed_q1] + 1
            elif ((close_date > pdate_plus_3mos) and (close_date <= pdate_plus_6mos)):
                # closed 3-6 months after pdate
                bus[fi.label] = fi.closed_q2
                class_counts[fi.closed_q2] = class_counts[fi.closed_q2] + 1
            elif ((close_date > pdate_plus_6mos) and (close_date <= pdate_plus_9mos)):
                # closed 6-9 months after pdate
                bus[fi.label] = fi.closed_q3
                class_counts[fi.closed_q3] = class_counts[fi.closed_q3] + 1
            elif ((close_date > pdate_plus_9mos) and (close_date <= pdate_plus_12mos)):
                # closed 9-12 months after pdate
                bus[fi.label] = fi.closed_q4
                class_counts[fi.closed_q4] = class_counts[fi.closed_q4] + 1
    # end for

    if (verbose):
        print '  number of businesses that passed date filter: %d' % len(buses.values())
        for i in xrange(5):
            print '    class %1d: %5d' % (i,class_counts[i])
    # end verbose

    qtr_boundary = [0,0,0,0,0]
    qtr_boundary[0] = pdate-12*month # start of prior year 1th quarter
    qtr_boundary[1] = pdate -9*month # start of prior year 2nd quarter
    qtr_boundary[2] = pdate -6*month # start of prior year 3rd quarter
    qtr_boundary[3] = pdate -3*month # start of prior year 4th quarter
    qtr_boundary[4] = pdate          # end of prior year 4st quarter

    # filter reviews that do not pertain to one of the remaining businesses or
    # were not submitted before pdate
    all_rev_count = 0
    qtr_rev_counts = [0, 0, 0, 0]
    for review in all_reviews:
        # look for the reviewed business
        bid = review[fi.business_id]
        obj = buses.get(bid, None)

        # update review_count, star_count and star_total for the business
        if (obj is not None):
            rdate = review[fi.date]
            if (rdate <= pdate):
                all_rev_count = all_rev_count + 1

                # update overall review count
                rcount = obj.get(fi.review_count,0)
                obj[fi.review_count] = rcount + 1
                # update overall star total
                stars = review.get(fi.stars,0)
                stotal = obj.get(fi.star_total,0)
                obj[fi.star_total] = stotal + stars

                # update the quarterly review counts and star totals
                for qtr in xrange(4):
                    if ((rdate > qtr_boundary[qtr]) and (rdate <= qtr_boundary[qtr+1])):
                        # review submitted during this quarter
                        qtr_rev_counts[qtr] = qtr_rev_counts[qtr] + 1
                        # update review count for this quarter
                        qtr_rcount = obj.get(fi.qtr_review_count[qtr],0)
                        obj[fi.qtr_review_count[qtr]] = qtr_rcount + 1
                        # update star total for this quarter
                        qtr_stotal = obj.get(fi.qtr_star_total[qtr],0)
                        obj[fi.qtr_star_total[qtr]] = qtr_stotal + stars
                        # don't need to check the other quarters for this review
                        break
    # end for

    if (verbose):
        print '  number of reviews that passed filter: %d' % all_rev_count
        for i in xrange(4):
            print '    review count q%1d: %5d' % (i+1,qtr_rev_counts[i])
    # end verbose

    # filter tips that do not pertain to one of the remaining businesses or
    # were not submitted before pdate
    all_tip_count = 0
    qtr_tip_counts = [0, 0, 0, 0]
    for tip in all_tips:
        # look for the reviewed business
        bid = tip[fi.business_id]
        obj = buses.get(bid, None)

        # update tip_count for the business
        if (obj is not None):
            tdate = tip[fi.date]
            if (tdate <= pdate):
                all_tip_count = all_tip_count + 1

                # update overall tip count
                tcount = obj.get(fi.tip_count,0)
                obj[fi.tip_count] = tcount + 1

                # update quarterly tip counts
                for qtr in xrange(4):
                    if ((tdate > qtr_boundary[qtr]) and (tdate <= qtr_boundary[qtr+1])):
                        # tip submitted during this quarter
                        qtr_tip_counts[qtr] = qtr_tip_counts[qtr] + 1
                        # update review count for this quarter
                        qtr_tcount = obj.get(fi.qtr_tip_count[qtr],0)
                        obj[fi.qtr_tip_count[qtr]] = qtr_tcount + 1
                        # don't need to check the other quarters for this tip
                        break

    # end for

    if (verbose):
        print '  number of tips that passed filter: %d' % all_tip_count
        for i in xrange(4):
            print '    tip count q%1d: %5d' % (i+1,qtr_tip_counts[i])
    # end verbose

    # add census data
    # TBD

    # add economic data
    # TBD

    # if undersampling determine weight to use for under sampling the "still open" class
    if (usamp):
        # get size of largest "closed" class
        target_size = np.max(class_counts[fi.closed_q1:fi.closed_q4])
        # calculate the percentage of "still open" records that should be kept
        weight = float(target_size)/float(class_counts[fi.still_open])
        if (verbose):
            print '  weight for undersampling: %5.3f' % weight
        # reset class count for "still open" class
        class_counts[fi.still_open] = 0

    # calculate average star ratings, percent changes and remove unneeded attributes
    for bus in buses.values():
        # if undersampling determine whether this record should be kept
        if (usamp):
            label = bus[fi.label]
            if (label == fi.still_open):
                p = np.random.uniform(0.0, 1.0)
                if (p > weight):
                    # do not include this record in the data set
                    del buses[bus[fi.business_id]]
                    # go to the next business
                    continue
                else:
                    class_counts[fi.still_open] += 1

        # get overall review count
        rcount = bus.get(fi.review_count,0)

        # calculate overall average star rating
        if (rcount > 0):
            # get overall star total
            stotal = bus.get(fi.star_total,0)
            # calculate overall average star rating
            bus[fi.avg_star_rating] = float(stotal)/float(rcount)

        # calculate quarterly average star rating and quarterly percent changes
        for qtr in xrange(4):
            # calculate quarterly average star rating
            qtr_rcount = bus.get(fi.qtr_review_count[qtr],0)
            if (qtr_rcount > 0):
                qtr_stotal = bus.get(fi.qtr_star_total[qtr],0)
                bus[fi.qtr_avg_star_rating[qtr]] = float(qtr_stotal)/float(qtr_rcount)

            # calculate percent change for quarterly review counts, tip counts,
            # star total and average star ratings
            # - the average star ratings are calculated in this loop, so the
            #   next quarter value is not available during this iteration
            # - calculate using previous quarter and current quarter, so skip
            #   first iteration so a previous value is available for avg star rating
            if (qtr > 0):
                # quarterly review count percent change
                prev_qtr_rcount = bus.get(fi.qtr_review_count[qtr-1],0)
                bus[fi.qtr_review_count_pc[qtr-1]] = pct_change(prev_qtr_rcount, qtr_rcount)

                # quarterly tip count percent change
                qtr_tcount = bus.get(fi.qtr_tip_count[qtr],0)
                prev_qtr_tcount = bus.get(fi.qtr_tip_count[qtr-1],0)
                bus[fi.qtr_tip_count_pc[qtr-1]] = pct_change(prev_qtr_tcount, qtr_tcount)

                # quarterly star total percent change
                qtr_st = bus.get(fi.qtr_star_total[qtr],0)
                prev_qtr_st = bus.get(fi.qtr_star_total[qtr-1],0)
                bus[fi.qtr_star_total_pc[qtr-1]] = pct_change(prev_qtr_st, qtr_st)

                # quarterly average star rating percent change
                qtr_asr = bus.get(fi.qtr_avg_star_rating[qtr],0)
                prev_qtr_asr = bus.get(fi.qtr_avg_star_rating[qtr-1],0)
                bus[fi.qtr_avg_star_rating_pc[qtr-1]] = pct_change(prev_qtr_asr, qtr_asr)

        # filter out unneeded attributes
        jsonutils.filter_dict(bus, fi.data_feat_names, copy=False)

    # if undersampling then output the number of businesses in the "still open"
    # class that are remaining
    if (verbose and usamp):
        print '  number of businesses remaining after undersampling: %d' % len(buses.values())
        for i in xrange(5):
            print '    class %1d: %5d' % (i,class_counts[i])

    # return the final list of businesses
    return buses.values()

# end gen_dataset
'''
Filter the data from the Yelp! academic dataset so that it contains only objects
and attributes that are of interest.

Inputs:

  in_busjson:
    the path to the file containing JSON business objects

  out_busjson:
    the path to the file where the filtered JSON business objects will be written

  in_revjson:
    the path to the file containing JSON review objects

  out_revjson:
    the path to the file where the filtered JSON review objects will be written

  in_tipjson:
    the path to the file containing JSON tip objects

  out_tipjson
    the path to the file where the filtered JSON tip objects will be written

  in_demoeconcsv
    the path to the CSV file containing demographic and economic data for businesses

'''
def filter_yelp_data(in_busjson, out_busjson, in_revjson, out_revjson,
                     in_tipjson, out_tipjson, in_demoeconcsv):
    # initialize the column names
    #feat_columns = feat_info.data_feat_names
    bus_feats = fi.bus_feat_names
    rev_feats = fi.rev_feat_names
    tip_feats = fi.tip_feat_names
    
    # make sure the data features have been initialized
    #if (len(feat_columns)==0):
    #    print('\nWARNING: data features have not been initialized\n')
    
    # load the restaurant objects
    print 'loading business JSON objects from %s...' % in_busjson
    objects,junk = load_restaurants(in_busjson)

    # load the review and tip objects and add first/last review/tip date
    # and census tract to objects
    objects,reviews,tips = process_review_tip_census_data(in_revjson, in_tipjson,
                                                          in_demoeconcsv, objects)
    
    # create feature matrix
    #feat_mat, columns = get_feature_matrix(objects, feat_columns)
    
    # write the 2D feature array to file
    #print 'writing data features to %s...' % out_buscsv
    #write_feature_matrix_csv(out_buscsv, feat_mat, feat_columns)
    
    # write meta data to file
    print 'writing business JSON object to %s...' % out_busjson
    jsonutils.save_objects(objects, out_busjson, attfilt=bus_feats)

    # write review data to file
    print 'writing review JSON objects to %s...' % out_revjson
    jsonutils.save_objects(reviews, out_revjson, attfilt=rev_feats)

    # write tip data to file
    print 'writing tip JSON objects to %s...' % out_tipjson
    jsonutils.save_objects(tips, out_tipjson, attfilt=tip_feats)

'''
Collect the reviews and tips for the businesses in the specified list of
business objects.  Also, add the first and last review/tip dates and census
tract for each business in the specified list of business objects.

Inputs:

  in_revjson:
    the path to the file containing JSON review objects

  in_tipjson:
    the path to the file containing JSON tip objects

  in_demoeconcsv:
    the path to the CSV file containing demographic and economic data for businesses

  buses
    a list of dictionaties with each dictionary representing a business

Outputs:

  buses
    the list of business objects with each business object augmented with its
    first and last review dates and demographic and economic data

  reviews
    the list of reviews that were written for one of the businesses identified
    in the list of businesses passed as input

  tips
    the list of tips that were written for one of the businesses identified
    in the list of businesses passed as input
'''
def process_review_tip_census_data(in_revjson, in_tipjson, in_demoeconcsv, buses):
    # load the census tracts
    print 'loading demographic and economic data from %s...' % in_demoeconcsv
    demo_econ_data = csvutils.load_matrix(in_demoeconcsv,False)

    # initialize  dictionaries to hold the first and last review dates and
    # add lookup data for demo & econ data
    print 'initialize dictionaries...'
    first_review_dates = {}
    last_review_dates = {}
    demo_econ_lookup = {}
    for bus in buses:
        # add the business IDs for restaurants to the dictionaries
        bid = bus[fi.business_id]
        first_review_dates[bid] = None
        last_review_dates[bid] = None
        demo_econ_lookup[bid] = -1

    # initialize lookup table for demo and econ data
    print 'initialize lookup table for demographic and economic data...'
    for i in xrange(demo_econ_data.shape[0]):
        bid = demo_econ_data[i,fi.census_bus_id_idx]
        if (bid):
            demo_econ_lookup[bid] = i

    # collect the reviews that were written for one of the businesses in the list
    # of businesses and identify the first/last review/tip dates for each business
    reviews = []
    print 'processing reviews from %s...' % in_revjson
    with open(in_revjson, 'r') as fin:
        # there is one JSON object per line, iterate over the lines and load the JSON
        for line in fin:
            # load the JSON object as a dictionary
            review = json.loads(line)

            # if the review is for one of the requested businesses then update
            # the current first/last review/tip date for that business if necessary
            bid = review[fi.business_id]
            if (bid in last_review_dates):
                # append this review to the list of reviews
                reviews.append(review)
                # process review dates
                review_date = date2int(str2date(review[fi.date]))
                review[fi.date] = review_date
                # process first and last review/tip dates
                current_first = first_review_dates[bid]
                current_last = last_review_dates[bid]
                # if this review date is earlier than the current first review/tip
                # date then set the first review/tip date to this review date
                if (current_first is None or current_first > review_date):
                    first_review_dates[bid] = review_date
                # if this review date is more recent than the current last review/tip
                # date then set the last review/tip date to this review date
                if (current_last is None or current_last < review_date):
                    last_review_dates[bid] = review_date

    # collect the tips that were written for one of the businesses in the list
    # of businesses and update the first/last review/tip dates for each business
    tips = []
    print 'processing tips from %s...' % in_tipjson
    with open(in_tipjson, 'r') as fin:
        # there is one JSON object per line, iterate over the lines and load the JSON
        for line in fin:
            # load the JSON object as a dictionary
            tip = json.loads(line)

            # if the tip is for one of the requested businesses then update
            # the current first/last review/tip date for that business if necessary
            bid = tip[fi.business_id]
            if (bid in last_review_dates):
                # append this tip to the list of tips
                tips.append(tip)
                # process tip dates
                tip_date = date2int(str2date(tip[fi.date]))
                tip[fi.date] = tip_date
                # process first and last review/tip dates
                current_first = first_review_dates[bid]
                current_last = last_review_dates[bid]
                # if this tip date is earlier than the current first review/tip
                # date then set the first review/tip date to this review date
                if (current_first is None or current_first > tip_date):
                    first_review_dates[bid] = tip_date
                # if this tip date is more recent than the current last review/tip
                # date then set the last review/tip date to this review date
                if (current_last is None or current_last < tip_date):
                    last_review_dates[bid] = tip_date

    # copy the last review dates and census tracts into the business objects
    print 'adding first/last review date and census tract to business objects...'
    for bus in buses:
        bid = bus[fi.business_id]
        first_review_date = first_review_dates[bid]
        last_review_date = last_review_dates[bid]
        is_closed = not bus[fi.is_open]
        demo_econ_idx = demo_econ_lookup[bid]
        if (first_review_date is not None):
            bus[fi.first_review_date] = first_review_date
        if (last_review_date is not None):
            bus[fi.last_review_date] = last_review_date
            if (is_closed):
                bus[fi.close_date] = last_review_date
        if (demo_econ_idx >= 0):
            add_demo_econ_data(bus, demo_econ_data[demo_econ_idx,:])

    # return the augmented business objects, list of reviews and list of tips
    return buses, reviews, tips

'''
Add the demographic and economic data contained in the supplied vector
to the business object
'''
def add_demo_econ_data(bus, demo_econ_data):
    # add the demo & econ data to the business object
    bus[fi.census_tract]    = demo_econ_data[fi.census_tract_idx]
    bus[fi.income]          = demo_econ_data[fi.income_idx]
    bus[fi.census_pop]      = demo_econ_data[fi.census_pop_idx]
    bus[fi.census_black]    = demo_econ_data[fi.census_black_idx]
    bus[fi.census_young]    = demo_econ_data[fi.census_young_idx]
    bus[fi.census_old]      = demo_econ_data[fi.census_old_idx]
    bus[fi.competitors]     = demo_econ_data[fi.competitors_idx]
    bus[fi.competitors_pc]  = demo_econ_data[fi.competitors_pc_idx]
    bus[fi.census_black_pc] = demo_econ_data[fi.census_black_pc_idx]
    bus[fi.census_young_pc] = demo_econ_data[fi.census_young_pc_idx]
    bus[fi.census_old_pc]   = demo_econ_data[fi.census_old_pc_idx]
    bus[fi.income_pc]       = demo_econ_data[fi.income_pc_idx]
    bus[fi.income_group]    = demo_econ_data[fi.income_group_idx]

    return bus
# end add_demo_econ_data

# ==================================================
# Functions to load JSON objects from JSON files
# ==================================================
'''
Load restaurant objects from the specified JSON file path.

Inputs:

  file_path:
    the path the file containing JSON objects

Outputs:

  objects:
    list of JSON objects, the JSON objects are python dictionaries

  columns:
    list of keys that can be used to access JSON object attributes
'''
def load_restaurants(file_path):
    return jsonutils.load_objects(file_path, filt=fi.restaurant_filter)

# ==================================================
# Functions to convert data
# ==================================================
def str2date(datestr):
    return time.strptime(datestr, '%Y-%m-%d')

def date2str(date):
    return time.strftime('%Y-%m-%d', date)

def date2int(d):
    return int(time.mktime(d))

def int2date(secs):
    return time.localtime(secs)

# ==================================================
# Math functions
# ==================================================
def pct_change(old_val, new_val):
    if (np.allclose(old_val,new_val)):
        return 0
    elif (not np.allclose(old_val,0)):
        return float(new_val - old_val)/float(old_val)
    elif (not np.allclose(new_val,0)):
        return math.log(new_val) # - math.log(1)
    else:
        return 0.0