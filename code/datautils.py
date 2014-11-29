# -*- coding: utf-8 -*-
"""
This modules provides utility functions for working with the yelp academic
dataset data files.

Created on Wed Oct 29 18:31:04 2014

@author John Maloney (jmmaloney3@gmail.com)

Note: Some of the code in this module is based on code originally developed by
Scott Clark (scott@scottclark.io) and licensed under the Apache License,
Version 2.0:

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

'''
Load data for restaurants, convert the data features into numeric data and then
save the data features and meta data to the specified files.

Inputs:

  json_bus_path:
    the path to the file containing JSON business objects

  json_review_path
    the path to the file containing JSON review objects
  
  csv_tract_path
    the path to the CSV file containing cencus tracts for businesses

  feat_file_path:
    the path to the file where the csv feature data will be written

  meta_file_path:
    the path to the file where the csv meta data will be written

  rev_file_path
    the path to the file where the csv review data will be written
'''
def convert_restaurant_json_to_csv(json_bus_path, json_review_path, csv_tract_path, \
           feat_file_path, meta_file_path, rev_file_path):
    # initialize the column names
    feat_columns = feat_info.data_feat_names
    meta_columns = feat_info.meta_feat_names
    rev_columns = feat_info.review_feat_names
    
    # make sure the data features have been initialized
    if (len(feat_columns)==0):
        print('\nWARNING: data features have not been initialized\n')
    
    # load the restaurant objects
    print 'loading %s...' % json_bus_path
    objects,junk = load_restaurants(json_bus_path)

    # add last review date and census tract to objects
    objects,reviews = process_review_census_data(json_review_path, csv_tract_path, objects)
    
    # create feature matrix
    feat_mat = get_feature_matrix(objects, feat_columns)
    
    # write the 2D feature array to file
    print 'writing data features to %s...' % feat_file_path
    write_feature_matrix_csv(feat_file_path, feat_mat, feat_columns)
    
    # write meta data to file
    print 'writing meta features to %s...' % meta_file_path
    write_objects_csv(meta_file_path, objects, meta_columns)

    # write review data to file
    print 'writing review features to %s...' % rev_file_path
    write_objects_csv(rev_file_path, reviews, rev_columns)
'''
Collect the reviews for each business in the specified list of business objects.
Also, add the first and last review dates and census tract for each business in
the specified list of business objects.

Inputs:

  json_review_path
    the path to the file containing JSON review objects

  csv_tract_path
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
'''
def process_review_census_data(json_review_path, csv_tract_path, buses):
    # load the reviews
    # - the reviews don't indicate the usiness type - so have to load them all
    print 'loading %s...' % csv_tract_path
    census_data = read_feature_matrix_csv(csv_tract_path,False)

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
    # of businesses add identify the first/last review dates for each business
    reviews = []
    print 'processing reviews...'
    with open(json_review_path, 'r') as fin:
        # there is one JSON file per line, iterate over the lines and load the JSON
        for line in fin:
            # load the JSON object as a dictionary
            review = json.loads(line)

            # if the review is for one of the requested businesses then update
            # the current first/last review date for that business if necessary
            bid = review['business_id']
            if (bid in last_review_dates):
                # append this review to ethe list of reviews
                reviews.append(review)
                # process review dates
                review_date = str2date(review['date'])
                review['date'] = date2int(review_date)
                # process first and last review dates
                current_first = first_review_dates[bid]
                current_last = last_review_dates[bid]
                # if this review date is earlier than the current first review
                # date then set the first review date to this review date
                if (current_first is None or current_first > review_date):
                    first_review_dates[bid] = review_date
                # if this review date is more recent than the current last review
                # date then set the last review date to this review date
                if (current_last is None or current_last < review_date):
                    last_review_dates[bid] = review_date

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

    # return the augmented business objects and list of reviews
    return buses, reviews

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
    # there is one JSON file per line, iterate over the lines and load the JSON
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
# end load_json

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