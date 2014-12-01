# -*- coding: utf-8 -*-
"""
This modules provides utility functions for working with the CSV data files.

Created on Sun Nov 30 20:06:29 2014

@author: John Maloney
"""

import csv
import numpy as np

# ==================================================
# Functions to write matrices to CSV files
# ==================================================
'''
Save the specified 2D array to a CSV file.

Inputs:

  file_path:
    the path the file where the feature matrix should be written

  features:
    a 2D numpy float array containing one line for each object and one
    column for each feature

  columns:
    names of the attributes that are included in the feature matrix, this is
    used to write the names of the attributes to the file as column headers,
    all the columns in the feature matrix will be written to file regardless of
    the names in this list, if the list is None then the attribute names are not
    written to file
'''
def save_matrix(file_path, features, columns=None):
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

# ==================================================
# Functions to read matrices from CSV files
# ==================================================
'''
Load data from the specified CSV file into a 2D array.

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
def load_matrix(file_path, has_hdr=True):
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
# Functions to write JSON objects to CSV files
# ==================================================
'''
Write the specified JSON objects to a CSV file.

Inputs:

  file_path:
    the path the file containing JSON objects

  objects:
    list of JSON objects, the JSON objects are python dictionaries

  columns:
    list of keys for attributes to be written to the file, only the columns
    specified in this list will be written to the file
'''
def write_objects(file_path, objects, columns):
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
def get_row(obj, columns):
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

