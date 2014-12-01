# -*- coding: utf-8 -*-
"""
Created on Sun Nov  2 20:34:12 2014

@author: John Maloney
"""
import csv

# attribute names
business_id = 'business_id'
review_id = 'review_id'
tip_id = 'tip_id'
user_id = 'user_id'
label = 'label'
avg_star_rating = 'avg_star_rating'
review_count = 'review_count'
tip_count = 'tip_count'
date = 'date'
first_review_date = 'first_review_date'
last_review_date = 'last_review_date'
stars = 'stars'
likes = 'likes'
star_total = 'star_total'
state = 'state'
census_tract = 'census_tract'
restaurants = 'categories.Restaurants'
name = 'name'
full_address = 'full_address'
city = 'city'
latitude = 'latitude'
longitude = 'longitude'
open_attr = 'open'

# features included in datasets generated for specified prediction dates
pdate_dataset_feat_names = [label, avg_star_rating, review_count, tip_count]
# feat_info: key - attribute name, value - tuple with first entry providing the
#     type of the attribute and the second entry providing the default value
pdate_dataset_feat_info = {label:(int,-1),
                           avg_star_rating:(float,0.0),
                           review_count:(int,0),
                           tip_count:(int,0)}

data_feat_info = dict([])
data_feat_names = []

bus_feat_info = {business_id:(str,'MISSING'),
                 #name,(str,'MISSING'),
                 #full_address,(str,'MISSING'),
                 #city,(str,'MISSING'),
                 state:(str,'MISSING'),
                 #latitude,(float,-1.0),
                 #longitude,(float,-1.0),
                 #review_count,(int,0),
                 #open_attr,(int,True),
                first_review_date:(int,-1),
                last_review_date:(int,-1),
                census_tract:(int,-1)}

bus_feat_names = bus_feat_info.keys()

# filter used to filter business data
restaurant_filter = {restaurants:[True],
                     state:['AZ','NV','WI']}

# values for ordinal attributes
attire_values = [None, 'casual', 'dressy', 'formal']
noise_values =  [None, 'quiet', 'average', 'loud', 'very_loud']
ages_allowed_values = [None,'allages','18plus','21plus']
alcohol_values = [None,'none','beer_and_wine','full_bar']
byob_values = [None,'no','yes_corkage','yes_free']
smoking_values = [None,'no','outdoor','yes']
wifi_values = [None,'no','paid','free']

rev_feat_names = [review_id,business_id,user_id,date,stars]
tip_feat_names = [business_id,user_id,date,likes]

'''
Load data features from the specified file.  The file can be found here:

  ../data/data_feats.csv
'''
def init_data_feats(file_path):
    # initialize the global module variables
    global data_feat_info
    global data_feat_names

    # reset the value of data_feats_info
    data_feat_info = dict([])
    data_feat_names = []
    
    with open(file_path, 'rbU') as fin:
        csv_file = csv.reader(fin)
        # read the features
        for row in csv_file:
            data_feat_info[row[0]] = (bool,False)
            data_feat_names.append(row[0])
        
        # set the type for ordinal attributes
        data_feat_info['attributes.Ages Allowed'] = (ages_allowed_values,None)
        data_feat_info['attributes.Attire'] = (attire_values,None)
        data_feat_info['attributes.Smoking'] = (smoking_values,None)
        data_feat_info['attributes.Wi-Fi'] = (wifi_values,None)
        data_feat_info['attributes.BYOB/Corkage'] = (byob_values,None)
        data_feat_info['attributes.Alcohol'] = (alcohol_values,None)
        data_feat_info['attributes.Noise Level'] = (noise_values,None)
        
        # set the type for numeric attributes
        data_feat_info[review_count] = (int,0)
        data_feat_info[stars] = (float,0.0)
        
        return data_feat_info,data_feat_names

# =================================================================
# Functions to write column/feature information to file as csv data
# =================================================================
'''
Write the feature names and possible values to a CSV file
'''
def write_columns_csv(file_path, objects, columns=data_feat_names):
    with open(file_path, 'wb+') as fout:
        csv_file = csv.writer(fout)
        # write column headers
        csv_file.writerow(['attribute','possible values'])
        for key in columns:
            # get the possible values for the feature
            values = get_feature_values(objects, key)
            # don't print out the possible values if there are a lot of them
            if (len(values) > 50):
                values = "various"
            else:
                values = map('\'{0}\''.format, values)
                values = ",".join(map(str, values))
            csv_file.writerow([key, '[{0}]'.format(values)])

'''
Get the possible values for the specified attribute.
'''
def get_feature_values(objects, key):
    return set( (obj[key] if (key in obj) else None) for obj in objects)