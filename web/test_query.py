#!/usr/bin/env python

import json

data = json.load(file("test_query.json"))

query = "time > {} and time < {}".format(data['time']['on'],
                                         data['time']['off'])

if 'dow' in data:
    dowquery = " or ".join(["dow == {}".format(d) for d in data['dow']])
    query = "({}) and ({})".format(query, dowquery)
elif 'dom' in data:
    if 'off' in data['dom']:
        domquery = "dom >= {} and dom <= {}".format(data['dom']['on'],
                                                    data['dom']['off'])
    else: # Only work for the 'on' day
        domquery = "dom == {}".format(data['dom']['on'])
    query = "({}) and ({})".format(query, domquery)
elif 'doy' in data:
    #doyentries = []
    #for k, v in data['doy']:
    #    doyentries.append("{} == {}".format(k, v))
    #doyquery = " and ".join(doyentries)
    doyquery = " and ".join(["{} == {}".format(k, v) for k, v in data['doy'].iteritems()])
    query = "({}) and ({})".format(query, doyquery)

if data['hierarchy'] == 'manual':
    query = "manual"
elif data['hierarchy'] == 'parent':
    query = "parent"
elif data['hierarchy'] == 'or':
    query = "({}) or parent".format(query)
elif data['hierarchy'] == 'and':
    query = "({}) and parent".format(query)
# If the type is 'own', no changes are made to the query.

print query
