# -*- coding: utf-8 -*-
"""
This modules provides utility functions for working with the yelp academic
dataset data files.

Created on Wed Oct 29 18:31:04 2014

@author John Maloney

Note: Some of the code in this module is based on code originally developed by
Scott Clark and licensed under the Apache License, Version 2.0:

    http://www.apache.org/licenses/LICENSE-2.0

The original source can be found here:

    https://github.com/Yelp/dataset-examples/blob/master/json_to_csv_converter.py

This modified version is based on the original version submitted on Oct 16, 2014.
"""

import numpy as np
import json
import csv
import feat_info
import time
import io

'''
Generate a data set that contains values that were available on the specified
date.

Inputs:

  pdate
    the prediction date to use for generating the dataset (an int expressed as
    seconds since the epoch)

  busjson:
    the path to the file containing JSON business objects

  revjson:
    the path to the file containing JSON review objects

  tipjson:
    the path to the file containing JSON tip objects
'''
def gen_dataset(pdate, busjson, revjson, tipjson):
    # calculate duration of time periods in seconds
    # - 30 days x 24 hrs/day x 60 min/hr x 60 sec/min
    month = 30*24*60*60
    pdate_plus_3mos  =  pdate+3*month
    pdate_plus_6mos  =  pdate+6*month
    pdate_plus_9mos  =  pdate+9*month
    pdate_plus_12mos = pdate+12*month

    # load business objects
    print 'Loading business objects from %s...' % busjson
    all_objects, all_columns = load_objects(busjson)

    # filter businesses that were not open before pdate or closed before pdate
    # and set the class label for those that remain
    objects = {}
    for obj in all_objects:
        open_date = obj['first_review_date']
        close_date = obj['last_review_date']
        if ((open_date <= pdate) and (close_date > pdate)):
            # business meets the criteria - add to dictionary
            objects[obj['business_id']]=obj
            # set class label for business
            if ((close_date > pdate) and (close_date <= pdate_plus_3mos)):
                # closed 0-3 months after pdate
                obj['class'] = 0
            elif ((close_date > pdate_plus_3mos) and (close_date <= pdate_plus_6mos)):
                # closed 3-6 months after pdate
                obj['class'] = 1
            elif ((close_date > pdate_plus_6mos) and (close_date <= pdate_plus_9mos)):
                # closed 6-9 months after pdate
                obj['class'] = 2
            elif ((close_date > pdate_plus_9mos) and (close_date <= pdate_plus_12mos)):
                # closed 9-12 months after pdate
                obj['class'] = 3
            elif (close_date > pdate_plus_12mos):
                # still open 12 months after pdate
                obj['class'] = 4
    # end for

    # load review objects
    print 'loading review objects from %s...' % revjson
    all_reviews = load_objects(revjson)

    # filter reviews that do not pertain to one of the remaining businesses or
    # were not submitted before pdate
    for review in all_reviews:
        # look for the reviewed business
        bid = review['business_id']
        obj = objects.get(bid, None)

        # update review_count, star_count and star_total for the business
        if (obj is not None):
            rdate = review['date']
            if (rdate <= pdate):
                # update review count
                rcount = obj.get('review_count',0)
                obj['review_cont'] = rcount + 1
                # update star count
                scount = obj.get('star_count',0)
                obj['star_count'] = scount + 1
                # update star total
                stars = review['stars']
                stotal = obj.get('star_total',0)
                obj['star_total'] = stotal + stars
    # end for

    # load tip objects
    print 'loading tip objects from %s...' % tipjson
    all_tips = load_objects(tipjson)

    # filter tips that do not pertain to one of the remaining businesses or
    # were not submitted before pdate
    for tip in all_tips:
        # look for the reviewed business
        bid = tip['business_id']
        obj = objects.get(bid, None)

        # increment tip cunt for the business
        if (obj is not None):
            tdate = tip['date']
            if (tdate <= pdate):
                tcount = obj.get('tip_count',0)
                obj['tip_cont'] = tcount + 1
    # end for

    # add census data
    # TBD

    # add economic data
    # TBD

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
    bus_feats = feat_info.bus_feat_names
    rev_feats = feat_info.rev_feat_names
    tip_feats = feat_info.tip_feat_names
    
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
    #feat_mat = get_feature_matrix(objects, feat_columns)
    
    # write the 2D feature array to file
    #print 'writing data features to %s...' % out_buscsv
    #write_feature_matrix_csv(out_buscsv, feat_mat, feat_columns)
    
    # write meta data to file
    print 'writing business JSON object to %s...' % out_busjson
    save_objects(objects, out_busjson, attfilt=bus_feats)

    # write review data to file
    print 'writing review JSON objects to %s...' % out_revjson
    save_objects(reviews, out_revjson, attfilt=rev_feats)

    # write tip data to file
    print 'writing tip JSON objects to %s...' % out_tipjson
    save_objects(tips, out_tipjson, attfilt=tip_feats)
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
    census_data = read_feature_matrix_csv(in_censuscsv,False)

    # initialize  dictionaries to hold the last review dates and census tract
    print 'initialize dictionaries...'
    first_review_dates = {}
    last_review_dates = {}
    census_tracts = {}
    for bus in buses:
        bid = bus['business_id']
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
    print 'processing reviews...'
    with open(in_revjson, 'r') as fin:
        # there is one JSON object per line, iterate over the lines and load the JSON
        for line in fin:
            # load the JSON object as a dictionary
            review = json.loads(line)

            # if the review is for one of the requested businesses then update
            # the current first/last review/tip date for that business if necessary
            bid = review['business_id']
            if (bid in last_review_dates):
                # append this review to the list of reviews
                reviews.append(review)
                # process review dates
                review_date = str2date(review['date'])
                review['date'] = date2int(review_date)
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
    print 'processing tips...'
    with open(in_tipjson, 'r') as fin:
        # there is one JSON object per line, iterate over the lines and load the JSON
        for line in fin:
            # load the JSON object as a dictionary
            tip = json.loads(line)

            # if the tip is for one of the requested businesses then update
            # the current first/last review/tip date for that business if necessary
            bid = tip['business_id']
            if (bid in last_review_dates):
                # append this tip to the list of tips
                tips.append(tip)
                # process tip dates
                tip_date = str2date(tip['date'])
                tip['date'] = date2int(tip_date)
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
        bid = bus['business_id']
        first_review_date = first_review_dates[bid]
        last_review_date = last_review_dates[bid]
        tract = census_tracts[bid]
        if (first_review_date is not None):
            bus['first_review_date'] = date2int(last_review_date)
        if (last_review_date is not None):
            bus['last_review_date'] = date2int(last_review_date)
        if (tract is not None):
            bus['census_tract'] = tract

    # return the augmented business objects, list of reviews and list of tips
    return buses, reviews, tips

# ==================================================
# Functions to load feature matrices from JSON files
# ==================================================
'''
Load a restaurant feature matrix from the specified JSON file path.

Inputs:

  file_path:
    the path the file containing JSON objects
  
  columns: (optional)
    the columns to include in the feature matrix, by default all columns
    in the ``feat_info.data_feat_names`` are included

Outputs:

  features:
    a 2D numpy float array containing one line for each object and one
    column for each feature
'''
def load_restaurant_feature_matrix(file_path,columns=feat_info.data_feat_names):
    return load_feature_matrix(file_path, columns=columns,
                               filt=feat_info.restaurant_filter)

'''
Load a feature matrix from the specified JSON file path.

Inputs:

  file_path:
    the path the file containing JSON objects

  columns: (optional)
    the columns to include in the feature matrix, by default all columns
    in the ``data_feat_names`` are included

  filter_key: (optional)
    a key in the JSON file that will be used for filtering

  filter_val: (optional)
    the value to use for filtering, only objects where
    ``obj[filter_key] == filter_val`` will be returned

Outputs:

  features:
    a 2D numpy float array containing one line for each object and one
    column for each feature
'''
def load_feature_matrix(file_path,columns=feat_info.data_feat_names,filt=None):
    with open(file_path, 'r') as fin:
        # load the feature matrix from the JSON file
        return read_feature_matrix(fin,columns,filt)

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
    return load_objects(file_path, filt=feat_info.restaurant_filter)

'''
Load objects from the specified JSON file path and flatten the attributes into
a single level dictionary.

Inputs:

  file_path:
    the path the file containing JSON objects

  filt: (optional)
    dictionary containing the criteria that will be used to filter the
    objects that are loaded, each dictonary key is the name of a JSON
    attributes and each value is a list of possible values for that attribute,
    for each key-value pair the following condition is evaluated: obj[key] in value,
    each key-value pair defines criteria that are ORed together while the
    key-value pair conditons are ANDed together

Outputs:

  objects:
    list of JSON objects, the JSON objects are python dictionaries

  columns:
    list of keys that can be used to access JSON object attributes
'''
def load_objects(file_path, filt=None):
    with open(file_path, 'r') as fin:
        return read_objects(fin, filt)

# ==================================================
# Functions to save JSON objects to file
# ==================================================
'''
Save the JSON objects to the specified file path.

Inputs:

  objects:
    a list of dictionaries to write to file as JSON objects

  file_path:
    the path to the file where the JSON objects should be written

  filt: (optional)
    dictionary containing the criteria that will be used to filter the
    objects that are saved, each dictonary key is the name of a JSON
    attributes and each value is a list of possible values for that attribute,
    for each key-value pair the following condition is evaluated: obj[key] in value,
    each key-value pair defines criteria that are ORed together while the
    key-value pair conditons are ANDed together

  attfilt: (optional)
    a list of the names of the attributes to be written to file
'''
def save_objects(objects, file_path, filt=None, attfilt=None):
    with io.open(file_path, 'w', encoding='utf-8') as fout:
        return write_objects(objects, fout, filt, attfilt)

# ====================================================
# Functions to read feature matrices from file objects
# ====================================================
'''
Read a feature matrix from the specified file object containing JSON objects.

Inputs:

  file_path:
    the path the file containing JSON objects

  columns: (optional)
    the columns to include in the feature matrix, by default all columns
    in the ``data_feat_names`` are included

  filt: (optional)
    dictionary containing the criteria that will be used to filter the
    objects that are loaded, each dictonary key is the name of a JSON
    attributes and each value is a list of possible values for that attribute,
    for each key-value pair the following condition is evaluated: obj[key] in value,
    each key-value pair defines criteria that are ORed together while the
    key-value pair conditons are ANDed together

Outputs:

  features:
    a 2D numpy float array containing one line for each object and one
    column for each feature
'''
def read_feature_matrix(fin,columns=feat_info.data_feat_names,filt=None):
    # load the objects from the JSON file
    objects,junk = read_objects(fin, filt)

    # return features
    return get_feature_matrix(objects,columns)    

'''
Convert the specified list of JSON objects into a feature matrix.

Inputs:

  objects:
    the list of JSON objects (python dictionaries), one row will be added to
    feature matrix for each object
    
  columns: (optional)
    the columns to include in the feature matrix, by default all columns
    in ``feat_info.data_feat_names`` are included

Outputs:

  features:
    a 2D numpy float array containing one line for each object and one
    column for each feature
'''
def get_feature_matrix(objects, columns=feat_info.data_feat_names):
    # get the number of restaurants
    N = len(objects)
    
    # get the dimension
    D = len(columns)
    
    # add features to numpy array
    features = np.zeros((N,D),dtype=float)
    for obj,i in zip(objects, xrange(N)):
        for j in xrange(D):
            key = columns[j]
            dtype = feat_info.data_feat_info[key] \
                    if (key in feat_info.data_feat_info) else None
            features[i,j] = get_value(obj, key, dtype)

    # return the result as a 2D numpy array
    return features

'''
Read the value for the specified key and convert it to the specified data type.

Input:

  obj:
    a python dictionary representing a JSON object
  
  key:
    the key to use to access the value

  dtype:
    the data type to return, the valeu will be converted to this type
'''
def get_value(obj, key, dtype):
    val = obj[key] if (key in obj) else None
    if (dtype == bool):
        return bool(val)
    elif (dtype == float):
        if (val is None):
            return float('nan')
        else:
            return float(val)
    elif (dtype == int):
        if (val is None):
            return float('nan')
        else:
            return int(val)
    elif (type(dtype) == list):
        # the first value in the list is always None
        # if None is selected set the value to -1
        # so subtract 1 from the index that is returned
        return dtype.index(val)-1
    else:
        print 'unsupported type: %s' % dtype
        return float('nan')

# ==================================================
# Functions to read JSON objects from file objects
# ==================================================
'''
Read JSON objects from the specified file object and flatten the attributes
into a single level dictionary.

Inputs:

  fin:
    a file object from which JSON objects can be loaded

  filt: (optional)
    dictionary containing the criteria that will be used to filter the
    objects that are loaded, each dictonary key is the name of a JSON
    attributes and each value is a list of possible values for that attribute,
    for each key-value pair the following condition is evaluated: obj[key] in value,
    each key-value pair defines criteria that are ORed together while the
    key-value pair conditons are ANDed together

Outputs:

  objects:
    list of JSON objects, the JSON objects are python dictionaries

  columns:
    list of keys that can be used to access JSON object attributes
'''
def read_objects(fin, filt=None):
    # the list of objects to be populated
    objects = []
    # the list of columns to be populated
    columns = set()
    # there is one JSON object per line, iterate over the lines and load the JSON
    for line in fin:
        # load the JSON object as a dictionary
        line_contents = json.loads(line)
        # create a new dictionary to hold the flattened values
        obj = {}
        # flatten the values from the line_contents dictionary
        obj = flatten_dict(line_contents, obj)
        
        # set flag used to control whether this object is added
        passed_filter = True

        # apply the filter if appropriate
        if (filt is not None):
            # check the filter conditions
            for k,v in filt.iteritems():
                if ((k not in obj) or (obj[k] not in v)):
                    # this object doesn't pass the filter
                    passed_filter=False
                    # return to the parent loop
                    break

        # add the object to the list if it passed the filter
        if (passed_filter):
            # add the new object to the list
            objects.append(obj)
            # update the list of columns names
            columns.update(set(obj.keys()))

    return objects, columns
# end read_objects

'''
Flatten the keys in d and add them to obj.
'''
def flatten_dict(d, obj, parent_key=None):
    # iterate over the keys and values
    for child_key,val in d.iteritems():
        key = "{0}.{1}".format(parent_key, child_key) if parent_key else child_key
        if (type(val) == dict):
            obj = flatten_dict(val, obj, key)
        elif ((type(val) == list) or (type(val) == tuple)):
            # iterate over the items in the list and add a boolean attribute for each
            for item in val:
                item_key = "{0}.{1}".format(key, item) if key else item
                obj[item_key] = True
        else:
            # add the key,value pair to the dictionary
            obj[key] = val

    # return the updated obj and column list
    return obj

# ==================================================
# Functions to write JSON objects to file objects
# ==================================================
'''
Write JSON objects to the specified file object.

Inputs:

  objects:
    a lit of the JSON objects to be written to file

  fout:
    a file object to which JSON objects can be written

  filt: (optional)
    dictionary containing the criteria that will be used to filter the
    objects that are written, each dictonary key is the name of a JSON
    attributes and each value is a list of possible values for that attribute,
    for each key-value pair the following condition is evaluated: obj[key] in value,
    each key-value pair defines criteria that are ORed together while the
    key-value pair conditons are ANDed together

  attfilt: (optional)
    a list of the names of the attributes to be written to file
'''
def write_objects(objects, fout, filt=None, attfilt=None):
    # there is one JSON file per line, iterate over the lines and load the JSON
    for obj in objects:
        # set flag used to control whether this object is added
        passed_filter = True

        # apply the filter if appropriate
        if (filt is not None):
            # check the filter conditions
            for k,v in filt.iteritems():
                if ((k not in obj) or (obj[k] not in v)):
                    # this object doesn't pass the filter
                    passed_filter=False
                    # return to the parent loop
                    break

        # filter the attributes
        if (passed_filter and (attfilt is not None)):
            for key in obj.keys():
                if (key not in attfilt):
                    obj.pop(key, None)

        # add the object to the list if it passed the filter
        if (passed_filter):
            # write the object to the file
            fout.write(unicode(json.dumps(obj,ensure_ascii=False)))
    # end for
# end write_objects

# ==================================================
# Functions to read/write feature matrix as csv data
# ==================================================
'''
Write the specified feature matrix to a CSV file.

Inputs:

  file_path:
    the path the file where the feature matrix should be written

  features:
    a 2D numpy float array containing one line for each object and one
    column for each feature

  columns:
    names of the attributes that are included in the feature matrix, all the
    columns in the feature matrix will be written to file regardless of the 
    names in this list, if the list is None then the attribute names are not
    written to file
'''
def write_feature_matrix_csv(file_path, features, columns=None):
    with open(file_path, 'wb+') as fout:
        csv_file = csv.writer(fout)
        # write column headers
        if (columns is not None):
            csv_file.writerow(list(columns))
        # get number of samples
        N = features.shape[0]
        # write each row to file
        for i in xrange(N):
            csv_file.writerow(features[i,:])

'''
Read data from the specified CSV file into a feature matrix.

Inputs:

  file_path:
    the path to the file holding the data to be loaded

  has_hdr: (optional)
    indicates whether or not the file contains headers, by default this is True

Outputs:

  features:
    a 2D numpy array containing one line for each object and one
    column for each feature
'''
def read_feature_matrix_csv(file_path, has_hdr=True):
    with open(file_path, 'rbU') as fin:
        csv_file = csv.reader(fin)

        if (has_hdr):
            # skip column headers
            csv_file.next()

        # read the sample data
        data = []
        for row in csv_file:
            data.append(row)

        # convert the list to an numpy 2D array and return
        return np.array(data)

# ==================================================
# Functions to write objects to file as csv data
# ==================================================
'''
Write the specified features to a CSV file.

Inputs:

  file_path:
    the path the file containing JSON objects

  objects:
    list of JSON objects, the JSON objects are python dictionaries

  columns:
    list of keys for attributes to be written to the file
'''
def write_objects_csv(file_path, objects, columns=feat_info.data_feat_names):
    with open(file_path, 'wb+') as fout:
        csv_file = csv.writer(fout)
        # write column headers
        csv_file.writerow(list(columns))
        # write the selected features for each object
        for obj in objects:
            csv_file.writerow(get_row(obj, columns))

'''
Return a csv compatible row containing values for the specified columns.
'''
def get_row(obj, columns=feat_info.data_feat_names):
    row = []
    for key in columns:
        val = obj[key] if (key in obj) else None
        if isinstance(val, unicode):
            row.append('{0}'.format(val.encode('utf-8')))
        elif val is not None:
            row.append('{0}'.format(val))
        else:
            row.append('')
    return row

# ==================================================
# Functions to convert data
# ==================================================
def str2date(datestr):
    return time.strptime(datestr, '%Y-%m-%d')

def date2int(d):
    return int(time.mktime(d))