import pylab

pylab.title('Queries per lookup')
pylab.xlabel('Queries sent before T1')
pylab.ylabel('CDF')

output_filename = 'plots/cdf_l_queries_t1.eps'

lines_to_plot = (
    ('0.l_queries_till_peers.cdf', '0', 'r'),
    ('1.l_queries_till_peers.cdf', '1', 'g:+'),
    ('2.l_queries_till_peers.cdf', '2', 'g:v'),
    ('3.l_queries_till_peers.cdf', '3', 'g:x'),
#    ('4.l_queries_till_peers.cdf', '4', 'r--'),
    ('5.l_queries_till_peers.cdf', '5', 'g:^'),
    ('6.l_queries_till_peers.cdf', '6', 'k-+'),
    ('7.l_queries_till_peers.cdf', '7', 'k-v'),
    ('8.l_queries_till_peers.cdf', '8', 'k-x'),
#    ('9.l_queries_till_peers.cdf', '9', 'c--'),
    ('10.l_queries_till_peers.cdf', '10', 'k-^'),
    )
#    (filename, label, style)

def plot():
    markevery = 300
    plots = []
    for filename, label, style in lines_to_plot:
        x = []
        y = []
        for line in open('parser_results/' + filename):
            cum_str, value_str = line.split()
            y.append(float(cum_str))
            x.append(float(value_str))
        plots.append(pylab.semilogx(x, y, style, label=label,
                                    markevery=markevery))

    pylab.legend(loc='lower right')
    pylab.savefig(output_filename)
    pylab.close()

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()
