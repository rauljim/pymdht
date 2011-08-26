# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import sys

def cdf(results): 
    num_results = len(results)
    if num_results == 0:
        return []
    results.sort()
    step = 1. / num_results
    cum_values = []
    for i, v in enumerate(results):
        cum_values.append(((i+1) * step, v))
    return cum_values

def cdf_file(filename):
    output_filename = filename + '.cdf'
    results = [float(line[:-1]) for line in open(filename)]
    output_file = open(output_filename, 'w')
    for cum, value in cdf(results):
        output_file.write('%.4f\t%.4f\n' % (cum, value))

if __name__ == "__main__":
    for filename in sys.argv[1:]:
        print 'Processing %s ...' % (filename)
        sys.stdout.flush()
        cdf_file(filename)
        print 'DONE'


