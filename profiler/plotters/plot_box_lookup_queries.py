# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import pylab

pylab.title('Lookup Queries')
pylab.xlabel('Client')
pylab.ylabel('Lookup queries')

output_filename = 'box_lookup_queries.eps'

boxes_to_plot = (
    ('1.lookup_queries', 'ML'),
    ('2.lookup_queries', 'UT'),
    ('3.lookup_queries', 'BS'),
    ('4.lookup_queries', 'TR'),
    )
#    (filename, label)

xs = []
for box_to_plot in boxes_to_plot:
    filename, label= box_to_plot
    xs.append([float(line) for line in open(filename)])
boxplot = pylab.boxplot(xs)
labels = [v[1] for v in boxes_to_plot]
pylab.setp(pylab.gca(), 'xticklabels', labels)

pylab.savefig(output_filename)

print 'Output saved to:', output_filename


