import json
from datetime import datetime

def convert_business():
    busfile = open('yelp_academic_dataset_business.json')
    busfile_updated = open('yelp_academic_dataset_business_AZ_WI_NV.json', 'wb')

    business_ids = {}

    for business in busfile:
        business = json.loads(business)
        location = business['state']
        category = business['categories']
        if 'Restaurants' in category and (location=='WI' or location=='AZ' 
            or location=='NV'):
            json.dump(business, busfile_updated)
            business_ids[business['business_id']] = location
            busfile_updated.write('\n')

    busfile_updated.close()
    busfile.close()

    return business_ids

def convert_reviews(business_ids, dates):
    revfile = open('yelp_academic_dataset_review_AZ.json_preprocessed')
    revfile_updated = open('yelp_academic_dataset_review_AZ.json', 'wb')

    startdate1, enddate1, startdate2, enddate2 = dates

    for review in revfile:
        try:
            review = json.loads(review)
        except Exception, e:
            continue
        
        currdate = datetime.strptime(review['date'], '%Y-%m-%d')
        if review['business_id'] in business_ids and \
            business_ids[review['business_id']]=='AZ' and \
                ((currdate>=startdate1 and currdate<=enddate1) or\
                    (currdate>=startdate2 and currdate<=enddate2)):
            json.dump(review, revfile_updated)
            revfile_updated.write('\n')

    revfile_updated.close()
    revfile.close()

def convert_tips(business_ids, dates):
    tipfile = open('yelp_academic_dataset_tip_AZ.json_preprocessed')
    tipfile_updated = open('yelp_academic_dataset_tip_AZ.json', 'wb')

    startdate1, enddate1, startdate2, enddate2 = dates

    for tip in tipfile:
        try:
            tip = json.loads(tip)
        except Exception, e:
            continue

        currdate = datetime.strptime(tip['date'], '%Y-%m-%d')
        if tip['business_id'] in business_ids and \
            business_ids[tip['business_id']]=='AZ' and \
                ((currdate>=startdate1 and currdate<=enddate1) or\
                    (currdate>=startdate2 and currdate<=enddate2)):
            json.dump(tip, tipfile_updated)
            tipfile_updated.write('\n')

    tipfile_updated.close()
    tipfile.close()

if __name__ == '__main__':
    # Convert business file
    business_ids = convert_business()

    startdate1 = datetime.strptime('2010-07-01', '%Y-%m-%d')
    enddate1 = datetime.strptime('2010-12-31', '%Y-%m-%d')
    startdate2 = datetime.strptime('2011-07-01', '%Y-%m-%d')
    enddate2 = datetime.strptime('2011-12-31', '%Y-%m-%d')

    dates = startdate1, enddate1, startdate2, enddate2

    # Convert reviews file
    convert_reviews(business_ids, dates)

    # Convert tips file
    convert_tips(business_ids, dates)
