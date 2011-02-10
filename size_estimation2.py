#! /usr/bin/env python

import pylab

pylab.title('DHT size estimation')
pylab.xlabel('Time')
pylab.ylabel('Number of nodes (in millions)')

output_filename = 'size_estimation2.eps'

from core.identifier import Id


MAX_LOG_DISTANCE = 140
POINTS_PER_HOUR = 0.20
SECONDS_PER_SAMPLE = 30

time_between_points =  SECONDS_PER_SAMPLE/3600. #hours
num_samples_per_point = 120 #3600. / SECONDS_PER_SAMPLE / POINTS_PER_HOUR

print 'Time between points:', time_between_points
print 'Samples per point:', num_samples_per_point

multiplier = pow(2, 160 - 1 - MAX_LOG_DISTANCE)

def print_estimation(num_responses_list):
    avg = float(sum(num_responses_list)) / len(num_responses_list)
    size = multiplier * avg / 1000000
    print 'Estimation: %.2f M' % (
            size)
    




partial_num_queries = []
partial_num_responses = []
total_num_queries = []
total_num_responses = []

time = 0

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
    if len(partial_num_responses) == num_samples_per_point:
        xs.append(time) 
        avg = float(sum(partial_num_queries)) / len(partial_num_queries)
        ys_q.append(multiplier * avg / 1000000)
        avg = float(sum(partial_num_responses)) / len(partial_num_responses)
        ys_r.append(multiplier * avg / 1000000)

        print time,
        print_estimation(partial_num_responses)
        del partial_num_queries[0]
        del partial_num_responses[0]
    time = (time + time_between_points)# % 24

print len(partial_num_responses),
print_estimation(partial_num_responses)
        
print 'Final', 
print_estimation(total_num_responses)

#pylab.plot(xs, ys_q)
pylab.plot(xs, ys_r)
pylab.plot([1], [0])

pylab.savefig(output_filename)
print 'Output saved to:', output_filename
