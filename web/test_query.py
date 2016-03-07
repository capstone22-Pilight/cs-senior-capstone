#!/usr/bin/env python

from gen_query import gen_query

data = file("test_query.json").read()

query = gen_query(data)

print query
