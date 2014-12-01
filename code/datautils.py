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
import jsonutils
import csvutils

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

Outputs:

  buses:
    the JSON business objects selected for the dataset augmented with review
    and tip data (and eventually with census and economic data), a copy is made
    of the original JSON objects so that the objects in all_buses are not modified
'''
def gen_dataset(pdate, all_buses, all_reviews, all_tips):
    # calculate duration of time periods in seconds
    # - 30 days x 24 hrs/day x 60 min/hr x 60 sec/min
    month = 30*24*60*60
    pdate_plus_3mos  =  pdate+3*month
    pdate_plus_6mos  =  pdate+6*month
    pdate_plus_9mos  =  pdate+9*month
    pdate_plus_12mos = pdate+12*month

    # filter businesses that were not open before pdate or closed before pdate
    # and set the class label for those that remain
    buses = {}
    class_counts = [0, 0, 0, 0, 0]
    for orig_bus in all_buses:
        open_date = orig_bus.get(fi.first_review_date,None)
        close_date = orig_bus.get(fi.last_review_date,None)
        if ((open_date is not None) and (open_date <= pdate) and
            (close_date is not None) and (close_date > pdate)):
            # business meets the criteria - add a copy to dictionary
            bus = orig_bus.copy()
            buses[bus[fi.business_id]]=bus
            # set class label for business
            if ((close_date > pdate) and (close_date <= pdate_plus_3mos)):
                # closed 0-3 months after pdate
                bus[fi.label] = 0
                class_counts[0] = class_counts[0] + 1
            elif ((close_date > pdate_plus_3mos) and (close_date <= pdate_plus_6mos)):
                # closed 3-6 months after pdate
                bus[fi.label] = 1
                class_counts[1] = class_counts[1] + 1
            elif ((close_date > pdate_plus_6mos) and (close_date <= pdate_plus_9mos)):
                # closed 6-9 months after pdate
                bus[fi.label] = 2
                class_counts[2] = class_counts[2] + 1
            elif ((close_date > pdate_plus_9mos) and (close_date <= pdate_plus_12mos)):
                # closed 9-12 months after pdate
                bus[fi.label] = 3
                class_counts[3] = class_counts[3] + 1
            elif (close_date > pdate_plus_12mos):
                # still open 12 months after pdate
                bus[fi.label] = 4
                class_counts[4] = class_counts[4] + 1
    # end for

    print '  number of businesses that passed date filter: %d' % len(buses.values())
    for i in xrange(5):
        print '    class %1d: %5d' % (i,class_counts[i])

    # filter reviews that do not pertain to one of the remaining businesses or
    # were not submitted before pdate
    all_rev_count = 0
    for review in all_reviews:
        # look for the reviewed business
        bid = review[fi.business_id]
        obj = buses.get(bid, None)

        # update review_count, star_count and star_total for the business
        if (obj is not None):
            rdate = review[fi.date]
            if (rdate <= pdate):
                # update review count
                rcount = obj.get(fi.review_count,0)
                obj[fi.review_count] = rcount + 1
                # update star total
                stars = review.get(fi.stars,0)
                stotal = obj.get(fi.star_total,0)
                obj[fi.star_total] = stotal + stars

                all_rev_count = all_rev_count + 1
    # end for

    print '  number of reviews that passed filter: %d' % all_rev_count

    # filter tips that do not pertain to one of the remaining businesses or
    # were not submitted before pdate
    all_tip_count = 0
    for tip in all_tips:
        # look for the reviewed business
        bid = tip[fi.business_id]
        obj = buses.get(bid, None)

        # increment tip cunt for the business
        if (obj is not None):
            tdate = tip[fi.date]
            if (tdate <= pdate):
                tcount = obj.get(fi.tip_count,0)
                obj[fi.tip_count] = tcount + 1

                all_tip_count = all_tip_count + 1
    # end for

    print '  number of tips that passed filter: %d' % all_tip_count

    # add census data
    # TBD

    # add economic data
    # TBD

    # calculate average star ranking and remove unneeded attributes
    for bus in buses.values():
        # get review count and star total
        rcount = bus.get(fi.review_count,0)
        stotal = bus.get(fi.star_total,0)

        # calculate average star rating
        if (rcount > 0):
            bus[fi.avg_star_rating] = float(stotal)/float(rcount)

        # filter out unneeded attributes
        jsonutils.filter_dict(bus, fi.pdate_dataset_feat_names, copy=False)

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

  in_censuscsv
    the path to the CSV file containing cencus tracts for businesses

'''
def filter_yelp_data(in_busjson, out_busjson, in_revjson, out_revjson,
                     in_tipjson, out_tipjson, in_censuscsv):
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
                                                          in_censuscsv, objects)
    
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

  in_censuscsv:
    the path to the CSV file containing cencus tracts for businesses

  buses
    a list of dictionaties with each dictionary representing a business

Outputs:

  buses
    the list of business objects with each business object augmented with its
    last review date and census tract

  reviews
    the list of reviews that were written for one of the businesses identified
    in the list of businesses passed as input

  tips
    the list of tips that were written for one of the businesses identified
    in the list of businesses passed as input
'''
def process_review_tip_census_data(in_revjson, in_tipjson, in_censuscsv, buses):
    # load the census tracts
    print 'loading census tracts from %s...' % in_censuscsv
    census_data = csvutils.load_matrix(in_censuscsv,False)

    # initialize  dictionaries to hold the last review dates and census tract
    print 'initialize dictionaries...'
    first_review_dates = {}
    last_review_dates = {}
    census_tracts = {}
    for bus in buses:
        bid = bus[fi.business_id]
        # add the business IDs for restaurants to the dictionaries
        first_review_dates[bid] = None
        last_review_dates[bid] = None
        census_tracts[bid] = None

    # populate census tract data
    print 'processing census tracts...'
    for i in xrange(census_data.shape[0]):
        bid = census_data[i,0]
        tract = census_data[i,1]
        # add census tract
        if (tract): # is tract is not the empty string
            census_tracts[bid] = tract

    # collect the reviews that were written for one of the businesses in the list
    # of businesses add identify the first/last review/tip dates for each business
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
                review_date = str2date(review[fi.date])
                review[fi.date] = date2int(review_date)
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
    # of businesses add update the first/last review/tip dates for each business
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
                tip_date = str2date(tip[fi.date])
                tip[fi.date] = date2int(tip_date)
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
        tract = census_tracts[bid]
        if (first_review_date is not None):
            bus[fi.first_review_date] = date2int(first_review_date)
        if (last_review_date is not None):
            bus[fi.last_review_date] = date2int(last_review_date)
        if (tract is not None):
            bus[fi.census_tract] = tract

    # return the augmented business objects, list of reviews and list of tips
    return buses, reviews, tips

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

def date2int(d):
    return int(time.mktime(d))