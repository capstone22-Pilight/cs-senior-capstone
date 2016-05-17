import json

# Given a query data structure in JSON format, returns a query in the form of a boolean expression.
def gen_query(data):

    # If the query isn't valid JSON (or is empty), just return a "False" query.
    try:
        data = json.loads(data)
    except:
        return "False"

    # If a custom query is defined, just return that.
    custom = data.get('custom_query', "")
    if custom != "":
        return custom
    else:

        query = ""
        is_overnight = data['time']['off']['next_day']

        # Days of week
        dowquery_on = " or ".join(["dow == {}".format(d) for d in data['dow']])
        if is_overnight:
            # Shift the days over by 1 for the off time
            dowquery_off = " or ".join(["dow == {}".format((int(d)+1)%7) for d in data['dow']])
        else:
            dowquery_off = dowquery_on

        if len(data['dow']) > 1:
            dowquery_on = "({})".format(dowquery_on)
        if len(data['dow']) > 1:
            dowquery_off = "({})".format(dowquery_off)

        # Time
        timequeries = []
        if data['time']['on']['time'] != "":
            # If time is a number, quote it into a string
            if data['time']['on']['time'] in ["sunrise", "sunset"]:
                time = data['time']['on']['time']
            else:
                time = "'{}'".format(data['time']['on']['time'])

            # Build the query string with the qtime object
            qtimestr = "(time >= qtime({}".format(time)
            if data['time']['on']['early'] != "":
                qtimestr += ", early='{}'".format(data['time']['on']['early'])
            if data['time']['on']['late'] != "":
                qtimestr += ", late='{}'".format(data['time']['on']['late'])
            qtimestr += ")"

            # Also add in days of the week
            if len(dowquery_on) > 0:
                qtimestr += " and {})".format(dowquery_on)

            timequeries.append(qtimestr)

        if data['time']['off']['time'] != "":
            # If time is a number, quote it into a string
            if data['time']['off']['time'] in ["sunrise", "sunset"]:
                time = data['time']['off']['time']
            else:
                time = "'{}'".format(data['time']['off']['time'])

            # Build the query string with the qtime object
            qtimestr = "(time <= qtime({}".format(time)
            if data['time']['off']['early'] != "":
                qtimestr += ", early='{}'".format(data['time']['off']['early'])
            if data['time']['off']['late'] != "":
                qtimestr += ", late='{}'".format(data['time']['off']['late'])
            qtimestr += ")"

            # Also add in days of the week
            if len(dowquery_off) > 0:
                qtimestr += " and {})".format(dowquery_off)

            timequeries.append(qtimestr)

        if is_overnight:
            query += "({})".format(" or ".join(timequeries))
        else:
            query += "({})".format(" and ".join(timequeries))

        # Year/month/day range
        rangequeries = []
        if data['range']['on']['year'] != "":
            if data['range']['off']['year'] != "": # If an off setting is specified, use a range
                rangequeries.append("year >= {} and year <= {}".format(data['range']['on']['year'],
                                                                         data['range']['off']['year']))
            else: # Otherwise, only work for the 'on' setting
                rangequeries.append("year == {}".format(data['range']['on']['year']))
        if data['range']['on']['month'] != "":
            if data['range']['off']['month'] != "": # If an off setting is specified, use a range
                rangequeries.append("month >= {} and month <= {}".format(data['range']['on']['month'],
                                                                         data['range']['off']['month']))
            else: # Otherwise, only work for the 'on' setting
                rangequeries.append("month == {}".format(data['range']['on']['month']))
        if data['range']['on']['day'] != "":
            if data['range']['off']['day'] != "": # If an off setting is specified, use a range
                rangequeries.append("day >= {} and day <= {}".format(data['range']['on']['day'],
                                                                         data['range']['off']['day']))
            else: # Otherwise, only work for the 'on' setting
                rangequeries.append("day == {}".format(data['range']['on']['day']))

        if len(rangequeries) > 0:
            if len(query) > 0:
                query += " and "
            query += "({})".format(" and ".join(rangequeries))

        if data['hierarchy'] == 'manual':
            query = "manual"
        elif data['hierarchy'] == 'parent':
            query = "parent"
        elif data['hierarchy'] == 'or':
            if len(query) > 0:
                query = "({}) or parent".format(query)
            else:
                query = "parent"
        elif data['hierarchy'] == 'and':
            if len(query) > 0:
                query = "({}) and parent".format(query)
            else:
                query = "parent"
        # If the type is 'own', no changes are made to the query.

        # As a failsafe, if somehow the query is still empty, just make it False
        if len(query) == 0:
            query = "False"

        return query
