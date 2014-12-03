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
qtr_avg_star_rating = []
qtr_avg_star_rating.append('avg_star_rating_q1')
qtr_avg_star_rating.append('avg_star_rating_q2')
qtr_avg_star_rating.append('avg_star_rating_q3')
qtr_avg_star_rating.append('avg_star_rating_q4')
review_count = 'review_count'
qtr_review_count = []
qtr_review_count.append('review_count_q1')
qtr_review_count.append('review_count_q2')
qtr_review_count.append('review_count_q3')
qtr_review_count.append('review_count_q4')
tip_count = 'tip_count'
qtr_tip_count = []
qtr_tip_count.append('tip_count_q1')
qtr_tip_count.append('tip_count_q2')
qtr_tip_count.append('tip_count_q3')
qtr_tip_count.append('tip_count_q4')
date = 'date'
first_review_date = 'first_review_date'
last_review_date = 'last_review_date'
close_date = 'close_date'
stars = 'stars'
likes = 'likes'
star_total = 'star_total'
qtr_star_total = []
qtr_star_total.append('star_total_q1')
qtr_star_total.append('star_total_q2')
qtr_star_total.append('star_total_q3')
qtr_star_total.append('star_total_q4')
state = 'state'
census_tract = 'census_tract'
restaurants = 'categories.Restaurants'
name = 'name'
full_address = 'full_address'
city = 'city'
latitude = 'latitude'
longitude = 'longitude'
is_open = 'open'

# class labels
closed_0_3_mos = 0
closed_3_6_mos = 1
closed_6_9_mos = 2
closed_9_12_mos =3
open_12_mos =    4

# class names
class_names = ['closed in  0-3 mos',
               'closed in  3-6 mos',
               'closed in  6-9 mos',
               'closed in 9-12 mos',
               'open after 12 mos']

# feat_info: (used when calling jsonutils.json2xy)
#            key - attribute name
#            value - tuple with first entry providing the type of the attribute
#                    and the second entry providing the default value

# features included in datasets generated for specified prediction dates
data_feat_info = {label:(int,-1),
                  avg_star_rating:(float,0.0),
                  review_count:(int,0),
                  tip_count:(int,0)}
#for qtr in xrange(4):
#    data_feat_info[qtr_review_count[qtr]]=(int,0)
#    data_feat_info[qtr_tip_count[qtr]]=(int,0)
#    data_feat_info[qtr_avg_star_rating[qtr]]=(int,0)

data_feat_names = data_feat_info.keys()

# features included in business.json
bus_feat_info = {business_id:(str,'MISSING'),
                 #name,(str,'MISSING'),
                 #full_address,(str,'MISSING'),
                 #city,(str,'MISSING'),
                 state:(str,'MISSING'),
                 #latitude:(float,-1.0),
                 #longitude:(float,-1.0),
                 #review_count:(int,0),
                 is_open:(int,True),
                 first_review_date:(int,-1),
                 last_review_date:(int,-1),
                 close_date:(int,-1),
                 census_tract:(int,-1)}

bus_feat_names = bus_feat_info.keys()

# features included in review.json
rev_feat_names = [review_id,business_id,user_id,date,stars]

# features included in tip.json
tip_feat_names = [business_id,user_id,date,likes]

# filter used to filter business data
restaurant_filter = {restaurants:[True],
                     state:['AZ','NV','WI']}

yelp_feat_info = {}
yelp_feat_names = []

# values for ordinal attributes
attire_values = [None, 'casual', 'dressy', 'formal']
noise_values =  [None, 'quiet', 'average', 'loud', 'very_loud']
ages_allowed_values = [None,'allages','18plus','21plus']
alcohol_values = [None,'none','beer_and_wine','full_bar']
byob_values = [None,'no','yes_corkage','yes_free']
smoking_values = [None,'no','outdoor','yes']
wifi_values = [None,'no','paid','free']

'''
Load yelp features from the specified file.  The file can be found here:

  ../data/data_feats.csv
'''
def init_yelp_feats(file_path):
    # initialize the global module variables
    global yelp_feat_info
    global yelp_feat_names

    # reset the value of data_feats_info
    yelp_feat_info = {}
    yelp_feat_names = []
    
    with open(file_path, 'rbU') as fin:
        csv_file = csv.reader(fin)
        # read the features
        for row in csv_file:
            yelp_feat_info[row[0]] = (bool,False)
        
        # set the type for ordinal attributes
        yelp_feat_info['attributes.Ages Allowed'] = (ages_allowed_values,None)
        yelp_feat_info['attributes.Attire'] = (attire_values,None)
        yelp_feat_info['attributes.Smoking'] = (smoking_values,None)
        yelp_feat_info['attributes.Wi-Fi'] = (wifi_values,None)
        yelp_feat_info['attributes.BYOB/Corkage'] = (byob_values,None)
        yelp_feat_info['attributes.Alcohol'] = (alcohol_values,None)
        yelp_feat_info['attributes.Noise Level'] = (noise_values,None)
        
        # set the type for numeric attributes
        yelp_feat_info[review_count] = (int,0)
        yelp_feat_info[stars] = (float,0.0)

        yelp_feat_names = yelp_feat_info.keys()
        
        return yelp_feat_info,yelp_feat_names

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