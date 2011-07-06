#! /usr/bin/env python

import pylab

pylab.title('DHT size estimation')
pylab.xlabel('Time')
pylab.ylabel('Number of nodes (in millions)')

output_filename = 'size_estimation.eps'

from core.identifier import Id


MAX_LOG_DISTANCE = 139
POINTS_PER_HOUR = 4.
SECONDS_PER_SAMPLE = 30

time_between_points =  1. / POINTS_PER_HOUR #hours
num_samples_per_point = 3600. / SECONDS_PER_SAMPLE / POINTS_PER_HOUR


multiplier = pow(2, 160 - MAX_LOG_DISTANCE - 1)

def print_estimation(num_responses_list):
    avg = float(sum(num_responses_list)) / len(num_responses_list)
    size = multiplier * avg / 1000000
    print 'Estimation: %.2f M' % (
            size)
    




partial_num_queries = []
partial_num_responses = []
total_num_queries = []
total_num_responses = []

time = 16.5

xs = []
ys_q = []
ys_r = []

for i, line in enumerate(open('size_estimation.dat')):
    try:
        num_queries, num_responses = [int(x) for x in line.split()]
    except:
        break
    partial_num_queries.append(num_queries)
    partial_num_responses.append(num_responses)
    total_num_queries.append(num_queries)
    total_num_responses.append(num_responses)
    if i % num_samples_per_point == 0:
        xs.append(time) 
        avg = float(sum(partial_num_queries)) / len(partial_num_queries)
        ys_q.append(multiplier * avg / 1000000)
        avg = float(sum(partial_num_responses)) / len(partial_num_responses)
        ys_r.append(multiplier * avg / 1000000)

        print time,
        print_estimation(partial_num_responses)
        partial_num_queries = []
        partial_num_responses = []
        time = (time + time_between_points)# % 24

print len(partial_num_responses),
print_estimation(partial_num_responses)
        
print 'Final', 
print_estimation(total_num_responses)

#pylab.plot(xs, ys_q)
pylab.plot(xs, ys_r)

pylab.savefig(output_filename)
print 'Output saved to:', output_filename
