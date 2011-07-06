# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import pylab

pylab.title('Lookup Time')
pylab.xlabel('Client')
pylab.ylabel('Lookup time (s)')

output_filename = 'box_l_time_nofliers.eps'

boxes_to_plot = (
    ('0.l_time.cdf', '0'),
    ('1.l_time.cdf', '1'),
    ('2.l_time.cdf', '2'),
    ('3.l_time.cdf', '3'),
    ('4.l_time.cdf', '4'),
    ('5.l_time.cdf', '5'),
    ('5.l_time.cdf', '6'),
    ('5.l_time.cdf', '7'),
    ('5.l_time.cdf', '8'),
    )
#    (filename, label)


plots = []
xs = []
for box_to_plot in boxes_to_plot:
    filename, label = box_to_plot
    xs.append([float(line) for line in open(filename)])
boxplot = pylab.boxplot(xs, sym='')
labels = [v[1] for v in boxes_to_plot]
pylab.setp(pylab.gca(), 'xticklabels', labels)
pylab.savefig(output_filename)

print 'Output saved to:', output_filename

