# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import pylab

pylab.title('Lookup Queries')
pylab.xlabel('Client')
pylab.ylabel('Lookup queries')

output_filename = 'box_l_queries.eps'

boxes_to_plot = (
    ('0.l_queries', 'UT'),
    ('1.l_queries', 'NS1'),
    ('2.l_queries', 'NS2'),
    ('3.l_queries', 'NS3'),
    ('4.l_queries', 'NS4'),
    ('5.l_queries', 'NS5'),
    ('6.l_queries', 'NS6'),
    ('7.l_queries', 'NS7'),
    ('8.l_queries', 'NS8'),
#    ('9.l_queries', 'NS9'),
    )
#    (filename, label)

def plot():
    xs = []
    labels = []
    for filename, label in boxes_to_plot:
        xs.append([float(line) for line in open(filename)])
        labels.append(label)
    boxplot = pylab.boxplot(xs)
    pylab.setp(pylab.gca(), 'xticklabels', labels)

    pylab.savefig(output_filename)
    pylab.close()
    
    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()
