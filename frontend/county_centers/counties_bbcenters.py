import json
import numpy as np

# https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=&f=json

with open('counties.json', 'r') as fid:
	data = json.load(fid)

result = {}

for item in data["features"]:

	county = item['attributes']['county']

	x0 = 1e8
	x1 = -1e8
	y0 = 1e8
	y1 = -1e8

	rings = item['geometry']['rings']

	for r in rings:
		for p in r:
			if p[0] < x0:
				x0 = p[0]
			if p[0] > x1:
				x1 = p[0]
			if p[1] < y0:
				y0 = p[1]
			if p[1] > y1:
				y1 = p[1]

	result[county] = [(x0+x1)/2, (y0+y1)/2]

with open('counties_bbcenters.json', 'w') as fid:
	json.dump(result, fid, ensure_ascii=False)
