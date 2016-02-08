#!/usr/bin/env python

import json

data = json.load(file("test_query.json"))

query = "time > {} and time < {}".format(data['time']['on'],
                                         data['time']['off'])

dayqueries = []
if 'dow' in data:
    dayqueries.append(" or ".join(["dow == {}".format(d) for d in data['dow']]))
if 'dom' in data:
    if 'off' in data['dom']:
        dayqueries.append("(dom >= {} and dom <= {})".format(data['dom']['on'],
                                                           data['dom']['off']))
    else: # Only work for the 'on' day
        dayqueries.append("dom == {}".format(data['dom']['on']))
if 'doy' in data:
    dayqueries.append("(" + " and ".join(["{} == {}".format(k, v) for k, v in data['doy'].iteritems()]) + ")")
query = "({}) and ({})".format(query, " or ".join(dayqueries))

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
