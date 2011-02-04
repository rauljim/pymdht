#! /usr/bin/env python

import pylab

pylab.title('DHT size estimation')
pylab.xlabel('Time')
pylab.ylabel('Number of nodes (in millions)')

output_filename = 'size_estimation.eps'

from core.identifier import Id


MAX_LOG_DISTANCE = 140
PARTIAL = 60

multiplier = pow(2, 160 - MAX_LOG_DISTANCE - 1)

def print_estimation(num_responses_list):
    avg = float(sum(num_responses_list)) / len(num_responses_list)
    size = multiplier * avg / 1000000
    print 'Estimation: %.2f M' % (
            size)
    




partial_num_responses = []
total_num_responses = []

time = 16.5

xs = []
ys = []

for i, line in enumerate(open('size_estimation.dat')):
    try:
        num_queries, num_responses = [int(x) for x in line.split()]
    except:
        break
    partial_num_responses.append(num_responses)
    total_num_responses.append(num_responses)
    if i % PARTIAL == 0:
        xs.append(time)
        ys.append(multiplier * partial_num_responses / 1000000)

        print time,
        print_estimation(partial_num_responses)
        partial_num_responses = []
        time = (time + .5) % 24

print len(partial_num_responses),
print_estimation(partial_num_responses)
        
print 'Final', 
print_estimation(total_num_responses)

pylab.plot(xs, ys)

pylab.savefig(output_filename)
print 'Output saved to:', output_filename
