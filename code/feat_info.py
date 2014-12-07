# -*- coding: utf-8 -*-
"""
Created on Sun Nov  2 20:34:12 2014

@author: John Maloney
"""
import csv

# ===============
# Yelp! data

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
close_date = 'close_date'
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
is_open = 'open'

# attribute names for quarterly values from the year prior to the prediction date
# - py_q1 values cover the time period 9-12 months prior to prediction date
# - py_q2 values cover the time period 6-9 months prior to prediction date
# - py_q3 values cover the time period 3-6 months prior to prediction date
# - py_q4 values cover the time period 0-3 months prior to prediction date
qtr_avg_star_rating = []
qtr_avg_star_rating.append('avg_star_rating_py_q1')
qtr_avg_star_rating.append('avg_star_rating_py_q2')
qtr_avg_star_rating.append('avg_star_rating_py_q3')
qtr_avg_star_rating.append('avg_star_rating_py_q4')

qtr_review_count = []
qtr_review_count.append('review_count_py_q1')
qtr_review_count.append('review_count_py_q2')
qtr_review_count.append('review_count_py_q3')
qtr_review_count.append('review_count_py_q4')

qtr_tip_count = []
qtr_tip_count.append('tip_count_py_q1')
qtr_tip_count.append('tip_count_py_q2')
qtr_tip_count.append('tip_count_py_q3')
qtr_tip_count.append('tip_count_py_q4')

qtr_star_total = []
qtr_star_total.append('star_total_py_q1')
qtr_star_total.append('star_total_py_q2')
qtr_star_total.append('star_total_py_q3')
qtr_star_total.append('star_total_py_q4')

# quarterly percent change attribute names
# - py_q1_q2 are percent change from prior year q1 to prior year q2
# - py_q2_q3 are percent change from prior year q2 to prior year q3
# - py_q4_q3 are percent change from prior year q3 to prior year q4
qtr_avg_star_rating_pc = []
qtr_avg_star_rating_pc.append('avg_star_rating_%c_py_q1_q2')
qtr_avg_star_rating_pc.append('avg_star_rating_%c_py_q2_q3')
qtr_avg_star_rating_pc.append('avg_star_rating_%c_py_q3_q4')

qtr_review_count_pc = []
qtr_review_count_pc.append('review_count_%c_py_q1_q2')
qtr_review_count_pc.append('review_count_%c_py_q2_q3')
qtr_review_count_pc.append('review_count_%c_py_q3_q4')

qtr_tip_count_pc = []
qtr_tip_count_pc.append('tip_count_%c_py_q1_q2')
qtr_tip_count_pc.append('tip_count_%c_py_q2_q3')
qtr_tip_count_pc.append('tip_count_%c_py_q3_q4')

qtr_star_total_pc = []
qtr_star_total_pc.append('star_total_pc_py_q1_q2')
qtr_star_total_pc.append('star_total_pc_py_q2_q3')
qtr_star_total_pc.append('star_total_pc_py_q3_q4')

# ===================================
# Demographic and economic data
income = 'income'
income_pc = 'income_pc' # income per capita
income_group = 'inc_group'
census_pop = 'pop' # population
census_black = 'black'
census_young = 'young'
census_old = 'old'
census_bus_id = 'id' # the business id
competitors = 'competitors'
competitors_pc = 'competitors_pc'
census_black_pc = 'black_pc'
census_young_pc = 'young_pc'
census_old_pc = 'old_pc'

# features are listed in the order they appear in business_demo_info.csv
demo_econ_feat_names = [census_tract, income, census_pop, census_black,
                        census_young, census_old, census_bus_id, competitors,
                        competitors_pc, census_black_pc, census_young_pc, census_old_pc,
                        income_pc, income_group]

census_tract_idx = demo_econ_feat_names.index(census_tract)
income_idx = demo_econ_feat_names.index(income)
census_pop_idx = demo_econ_feat_names.index(census_pop)
census_black_idx = demo_econ_feat_names.index(census_black)
census_young_idx = demo_econ_feat_names.index(census_young)
census_old_idx = demo_econ_feat_names.index(census_old)
census_bus_id_idx = demo_econ_feat_names.index(census_bus_id)
competitors_idx = demo_econ_feat_names.index(competitors)
competitors_pc_idx = demo_econ_feat_names.index(competitors_pc)
census_black_pc_idx = demo_econ_feat_names.index(census_black_pc)
census_young_pc_idx = demo_econ_feat_names.index(census_young_pc)
census_old_pc_idx = demo_econ_feat_names.index(census_old_pc)
income_pc_idx = demo_econ_feat_names.index(income_pc)
income_group_idx = demo_econ_feat_names.index(income_group)

# class labels
closed_q1  = 0
closed_q2  = 1
closed_q3  = 2
closed_q4  = 3
still_open = 4

# class names
class_names = ['closed in Q1',   # closed 0-3 months following prediction date
               'closed in Q2',   # closed 3-6 months following prediction date
               'closed in Q3',   # closed 6-9 months following prediction date
               'closed in Q4',   # closed 9-12 months following prediction date
               'open after Q4']  # still open 12 months after the prediction date

# feat_info: (used when calling jsonutils.json2xy)
#            key - attribute name
#            value - tuple with first entry providing the type of the attribute
#                    and the second entry providing the default value

# features included in datasets generated for specified prediction dates
data_feat_info = {label:(int,-1),
                  star_total:(float,0.0),
                  avg_star_rating:(float,0.0),
                  review_count:(int,0),
                  tip_count:(int,0)}
for qtr in xrange(4):
    data_feat_info[qtr_review_count[qtr]]=(int,0)
    data_feat_info[qtr_tip_count[qtr]]=(int,0)
    data_feat_info[qtr_avg_star_rating[qtr]]=(float,0)
    data_feat_info[qtr_star_total[qtr]]=(float,0)
for qtr in xrange(3):
    data_feat_info[qtr_review_count_pc[qtr]]=(float,0)
    data_feat_info[qtr_tip_count_pc[qtr]]=(float,0)
    data_feat_info[qtr_avg_star_rating_pc[qtr]]=(float,0)
    data_feat_info[qtr_star_total_pc[qtr]]=(float,0)

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
                 census_tract:(int,-1),
                 income:(float,-1.0),
                 census_pop:(float,-1.0),
                 census_black:(float,-1.0),
                 census_young:(float,-1.0),
                 census_old:(float,-1.0),
                 competitors:(int,-1),
                 competitors_pc:(float,-1.0),
                 census_black_pc:(float,-1.0),
                 census_young_pc:(float,-1.0),
                 census_old_pc:(float,-1.0),
                 income_pc:(float,-1.0),
                 income_group:(int,-1)}

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