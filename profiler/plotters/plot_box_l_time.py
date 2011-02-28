# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import pylab

pylab.title('Lookup Time')
pylab.xlabel('Client')
pylab.ylabel('Lookup time (s)')

output_filename = 'plots/box_l_time.eps'

boxes_to_plot = (
    ('1.l_time', 'NS1'),
    ('2.l_time', 'NS2'),
    ('3.l_time', 'NS3'),
    ('4.l_time', 'NS4'),
    ('5.l_time', 'NS5'),
    )
#    (filename, label)


xs = []
for box_to_plot in boxes_to_plot:
    filename, label = box_to_plot
    xs.append([float(line) for line in open('parser_results/' + filename)])
boxplot = pylab.boxplot(xs)
labels = [v[1] for v in boxes_to_plot]
pylab.setp(pylab.gca(), 'xticklabels', labels)
pylab.savefig(output_filename)

print 'Output saved to:', output_filename

