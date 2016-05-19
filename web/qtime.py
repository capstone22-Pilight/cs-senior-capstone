#!/usr/bin/env python

import datetime

class qtime(object):
    # Takes a time of either a datetime object or a string of format "HH:MM"
    # (in 24-hour time), and optionally an "early" or "late" value of the same
    # format, which simply substracts or adds to the time.
    # Given both an early and a late value, the time will be randomized within
    # the range created based on a hash of the current day so that comparisons
    # are consistent in the short term.
    def __init__(self, time, early=None, late=None):
        if isinstance(time, datetime.datetime):
            self.time = time
        elif isinstance(time, str):
            # Use the current time, but with the hour and minute replaced with
            # the given hour and minute.
            curtime = datetime.datetime.now()
            dtime = datetime.datetime.strptime(time, "%H:%M")
            self.time = curtime.replace(hour=dtime.hour, minute=dtime.minute)
        else:
            raise TypeError("qtime() takes a datetime object or string of format '%H:%M'")

        self.early = None
        if early != None:
            e = map(int, early.split(':'))
            self.early = datetime.timedelta(hours=e[0], minutes=e[1])

        self.late = None
        if late != None:
            e = map(int, late.split(':'))
            self.late = datetime.timedelta(hours=e[0], minutes=e[1])

    def __repr__(self):
        return "qtime({}, early={}, late={})".format(repr(self.time), self.early, self.late)

    # Returns the current time represented by this object, automatically taking
    # early and late values into account.
    def gettime(self):
        # If we have both an early value and a late value, randomize within the
        # period based on a hash of the current day so that comparisons are
        # consistent in the short term.
        if self.early != None and self.late != None:
            timerange = self.early + self.late
            datehash = abs(int(hash(datetime.datetime.now().date()))) # Today's "random" number
            timerange_seconds = int(timerange.total_seconds())
            timerange_random = datehash % timerange_seconds # Get a "random" value between 0 and timerange_seconds
            timerange_random_delta = datetime.timedelta(seconds=timerange_random)
            return self.time - self.early + timerange_random_delta
        elif self.early != None:
            return self.time - self.early
        elif self.late != None:
            return self.time + self.late
        else:
            return self.time

    # Compare this QueryTime with a datetime object.
    def __cmp__(self, other):
        return cmp(self.gettime().time(), other.gettime().time())
