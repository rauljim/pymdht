import pylab

pylab.title('Maintenance Queries')
pylab.xlabel('Time (s)')
pylab.ylabel('Queries (cumulative)')

output_filename = 'plots/cum_m_queries.eps'

lines_to_plot = (
    ('0.cum_m_queries', 'UT', 'k-'),
    ('1.cum_m_queries', 'NS1', 'r-'),
    ('2.cum_m_queries', 'NS2', 'b:'),
    ('3.cum_m_queries', 'NS3', 'g'),
    ('4.cum_m_queries', 'NS4', 'y'),
    ('5.cum_m_queries', 'NS5', 'm'),
    ('6.cum_m_queries', 'NS6', 'c'),
    ('7.cum_m_queries', 'NS7', 'r'),
    ('8.cum_m_queries', 'NS8', 'b'),
#    ('9.cum_m_queries', 'NS9', 'b'),
    )
#    (filename, label, style)

def plot():
    plots = []
    xs = []
    for filename, label, style in lines_to_plot:
        x = []
        y = []
        for line in open('parser_results/' + filename):
            ts, num_queries = line.split()
            x.append(int(ts))
            y.append(int(num_queries))
        pylab.plot(x, y, style, label=label)

    pylab.legend(loc='upper left')
    pylab.savefig(output_filename)
    pylab.close()
    

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()
