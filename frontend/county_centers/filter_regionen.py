import json
import numpy as np

# https://public.opendatasoft.com/explore/dataset/landkreise-in-germany/export/

with open('landkreise-in-germany.json', 'r') as fid:
	data = json.load(fid)

result = {}

for item in data:
	try:
		id = item["fields"]["cca_2"]
		p = item["fields"]["geo_point_2d"]

		result[id] = p
	except:
		print(item["fields"]["name_2"], "has no id")

with open('landkreise_marker.json', 'w') as fid:
	json.dump(result, fid, ensure_ascii=False)





# https://public.opendatasoft.com/explore/dataset/landkreise-in-germany/export/

with open('bundesland.json', 'r') as fid:
	data = json.load(fid)

result = {}

for item in data:

	id = item["fields"]["gen"]
	p = item["fields"]["geo_point_2d"]

	result[id] = p

with open('bundeslaender_marker.json', 'w') as fid:
	json.dump(result, fid, ensure_ascii=False)
