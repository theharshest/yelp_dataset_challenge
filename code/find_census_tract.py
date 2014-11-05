"""
Find Census Tract for entities based on latitude and longitude

Steps:
	1. Load Data into matrix with lat and long
	2. Submit API Request
	3. Parse info to get Census tract id
	4. Write a CSV file with id, tract_id


"""

from urllib2 import Request, urlopen, URLError
import xml.etree.ElementTree as etree 
import csv

# Step 1
f = open("../data/yelp_restaurant_locations.csv")
reader = csv.reader(f)
headers = reader.next()
column = {}
for h in headers: 
  column[h] = []
for row in reader:
  for h, v in zip(headers, row):
    column[h].append(v)
# Step 2

dataWriter = csv.writer(open('../data/business_tracts.csv', 'w'), delimiter=',')

num = len(column['business_id'])
print num
for i in range(0,num):
  url = "http://data.fcc.gov/api/block/2010/find?latitude={lat}&longitude={lon}".format(lat=column['latitude'][i], lon=column['longitude'][i])
  request = Request(url)
  response = urlopen(request)
  tree = etree.fromstring(response.read())
  fips = tree[0].get('FIPS')
  dataWriter.writerow([column['business_id'][i],fips])
  print i
  print tree[2].get('name')

