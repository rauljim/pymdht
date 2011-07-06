import pylab

pylab.title('Maintenance Queries')
pylab.xlabel('Time (s)')
pylab.ylabel('Queries (cumulative)')

output_filename = 'plots/cum_m_queries.eps'

lines_to_plot = (
    ('0.cum_m_queries', 'UT', 'r'),
    ('1.cum_m_queries', '1', 'k'),
    ('2.cum_m_queries', '2', 'b'),
    ('3.cum_m_queries', '3', 'g'),
    ('4.cum_m_queries', '4', 'y'),
    ('5.cum_m_queries', '5', 'm'),
    ('6.cum_m_queries', '6', 'k:'),
    ('7.cum_m_queries', '7', 'b:'),
    ('8.cum_m_queries', '8', 'g:'),
    ('9.cum_m_queries', '9', 'y:'),
    ('10.cum_m_queries', '10', 'm:'),
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
