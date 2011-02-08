# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import sys

import pylab

pylab.title('Lookup Time')
pylab.xlabel('Time (s)')
pylab.ylabel('CDF')

output_filename = 'cdf_lookup_time.eps'

styles = (
    'ko-', 'kx-', 'k+-', 'k*-',
    )
#    (filename, label, style)


plots = []
for filename, style in zip(sys.argv[1:], styles):
    _, label, _ = filename.split('.', 2)
    x = []
    y = []
    for line in open(filename):
        cum_str, value_str = line.split()
        y.append(float(cum_str))
        x.append(float(value_str))
    plots.append(pylab.semilogx(x, y, style, label=label))

pylab.legend(loc='lower right')
#pylab.show()
pylab.savefig(output_filename)

print 'Output saved to:', output_filename

