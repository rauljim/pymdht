import pylab

pylab.title('Queries per lookup')
pylab.xlabel('Queries')
pylab.ylabel('CDF')

output_filename = 'cdf_l_queries.eps'

lines_to_plot = (
    ('0.l_queries.cdf', 'UT', 'k'),
    ('1.l_queries.cdf', 'NS1', 'r:'),
    ('2.l_queries.cdf', 'NS2', 'b:'),
    ('3.l_queries.cdf', 'NS3', 'r-.'),
    ('4.l_queries.cdf', 'NS4', 'r--'),
    ('5.l_queries.cdf', 'NS5', 'b-.'),
    ('6.l_queries.cdf', 'NS6', 'b--'),
    ('7.l_queries.cdf', 'NS7', 'g--'),
    ('8.l_queries.cdf', 'NS8', 'c--'),
    )
#    (filename, label, style)

def plot():
    plots = []
    for filename, label, style in lines_to_plot:
        x = []
        y = []
        for line in open(filename):
            cum_str, value_str = line.split()
            y.append(float(cum_str))
            x.append(float(value_str))
        plots.append(pylab.plot(x, y, style, label=label))

    pylab.legend(loc='lower right')
    pylab.savefig(output_filename)
    pylab.close()

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()
