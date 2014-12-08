# -*- coding: utf-8 -*-
"""
This modules provides utility functions for working with the JSON data files.

Created on Sun Nov 30 19:57:18 2014

@author: John Maloney
"""

import json
import io
import numpy as np
import scipy.stats as stats

# ==================================================
# Functions to load JSON objects from JSON files
# ==================================================
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

  attributes:
    list of keys that can be used to access JSON object attributes
'''
def load_objects(file_path, filt=None):
    with open(file_path, 'r') as fin:
        return read_objects(fin, filt)

'''
Read JSON objects from the specified file object and flatten the attributes
into a single level dictionary.

Note: Some of the code in this function is based on code originally developed by
Scott Clark and licensed under the Apache License, Version 2.0:

    http://www.apache.org/licenses/LICENSE-2.0

The original source can be found here:

    https://github.com/Yelp/dataset-examples/blob/master/json_to_csv_converter.py

This modified version is based on the original version submitted on Oct 16, 2014.

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

        # filter the attributes and get a copy of the filtered object
        if (passed_filter and (attfilt is not None)):
            obj = filter_dict(obj, attfilt, copy=True)

        # add the object to the list if it passed the filter
        if (passed_filter):
            # write the object to the file
            fout.write(unicode(json.dumps(obj,ensure_ascii=False,sort_keys=True))+'\n')
    # end for
# end write_objects

'''
Filter the keys in the dictionary.  If copy is True then returns a copy of the
original dictionary with the keys filtered.  Otherwise, the original is modified.
By default, a copy is made.
'''
def filter_dict(d, attfilt, copy=True):
    if (copy):
        d = d.copy()
    for key in d.keys():
        if (key not in attfilt):
            d.pop(key, None)
    return d

# =============================================================================
# Functions to convert JSON objects to examples matrix (X) and label vector (y)
# =============================================================================
'''
Convert the specified JSON data to examples (X) and class labels (y).  The
specified label attribute is used as the class label.

Inputs:

  json:
    a list of dictionaries representing JSON objects

  column_info:
    a mapping from attribute names to data types and default values used to
    identify the attributes that should be included in the matrix and the data
    type and default value for each attribute

  label_attr:
    the name of the attribute that holds the class label

  std: (optional)
    whether the attribute values should be standardized to have a mean of zero
    and a standard deviation of one (default is False)

Outputs:

  X:
    a sparse matrix containing the attribute values for the examples

  y:
    a sparse matrix with one column containing the class labels
'''
def json2xy(json, column_info, label_attr, std=False):
    # convert JSON into a feature matrix
    data, columns = get_matrix(json, column_info=column_info)

    # get the column index of the class label
    y_idx = columns.index(label_attr)
    
    # get the column indices of the non-class label attributes
    X_idx = []
    for i in xrange(len(columns)):
        if (i != y_idx):
            X_idx.append(i)
    
    # create the class label matrix
    y = data[:,y_idx]

    # create the example attributes matrix
    X = data[:,X_idx]
    if (std):
        # if a column contains all the same value then zscore will return nan
        # - add small amount of random noise to the matrix
        X = X + np.random.normal(0,0.0001,X.shape)
        # calculate zscores for the augmented elements in the array
        X = stats.zscore(X,axis=0)

    # return the result
    return X,y

# ==================================================
# Functions to load feature matrices from JSON files
# ==================================================
'''
Load a matrix from the specified JSON file path.

Inputs:

  file_path:
    the path the file containing JSON objects

  column_info:
    a mapping from attribute names to data types and default values used to
    identify the attributes that should be included in the matrix and the data
    type and default value for each attribute

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

  columns:
    a list of the attributes names, the placement of a column name in the list
    indicates the position of the column holding the corresponding attribute
'''
def load_matrix(file_path,column_info,filt=None):
    with open(file_path, 'r') as fin:
        # load the feature matrix from the JSON file
        return read_matrix(fin,column_info,filt)

# ====================================================
# Functions to read feature matrices from JSON files
# ====================================================
'''
Read a matrix from the specified file object containing JSON objects.

Inputs:

  file_path:
    the path the file containing JSON objects

  column_info:
    a mapping from attribute names to data types and default values used to
    identify the attributes that should be included in the matrix and the data
    type and default value for each attribute

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

  columns:
    a list of the attributes names, the placement of a column name in the list
    indicates the position of the column holding the corresponding attribute
'''
def read_matrix(fin,column_info,filt=None):
    # load the objects from the JSON file
    objects,junk = read_objects(fin, filt)

    # return features
    return get_matrix(objects,column_info)    

# ====================================================
# Functions to convert JSON objects into numpy arrays
# ====================================================
'''
Convert the specified list of JSON objects into a matrix.

Inputs:

  objects:
    the list of JSON objects (python dictionaries), one row will be added to
    feature matrix for each object
    
  column_info:
    a mapping from attribute names to data types and default values used to
    identify the attributes that should be included in the matrix and the data
    type and default value for each attribute

Outputs:

  features:
    a 2D numpy float array containing one line for each object and one
    column for each feature

  columns:
    a list of the attributes names, the placement of a column name in the list
    indicates the position of the column holding the corresponding attribute
'''
def get_matrix(objects, column_info):
    # get the number of restaurants
    N = len(objects)
    
    # get the dimension
    columns = column_info.keys()
    D = len(columns)

    # add features to numpy array
    features = np.zeros((N,D),dtype=float)
    for obj,i in zip(objects, xrange(N)):
        for j in xrange(D):
            key = columns[j]
            info = column_info[key] if (key in column_info) else (None,None)
            features[i,j] = get_value(obj, key, info[0], info[1])

    # return features and list of columns
    return features, columns

'''
Read the value for the specified key and convert it to the specified data type.

Input:

  obj:
    a python dictionary representing a JSON object
  
  key:
    the key to use to access the value

  dtype:
    the data type to return, the value will be converted to this type

  defval:
    the default value to return if the object doesn't contain the attribute
'''
def get_value(obj, key, dtype, defval):
    # if the object doesn't contain the attribute return the default
    if (key not in obj):
        return defval

    val = obj[key]
    
    # if the value is None return the default
    if (val is None):
        return defval

    if (dtype == bool):
        return bool(val)
    elif (dtype == float):
        return float(val)
    elif (dtype == int):
        return int(val)
    elif (type(dtype) == list):
        # the first value in the list is always None
        # if None is selected set the value to -1
        # so subtract 1 from the index that is returned
        return dtype.index(val)-1
    else:
        print 'unsupported type: %s' % dtype
        return float('nan')
