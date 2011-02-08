import pylab

pylab.title('Maintenance Queries')
pylab.xlabel('Time (s)')
pylab.ylabel('Queries (cumulative)')

output_filename = 'cum_m_queries.eps'

lines_to_plot = (
    ('0.cum_m_queries', 'UT', 'k'),
    ('1.cum_m_queries', 'NS1', 'r'),
    ('2.cum_m_queries', 'NS2', 'b'),
    ('3.cum_m_queries', 'NS3', 'g'),
    ('4.cum_m_queries', 'NS4', 'y'),
    ('5.cum_m_queries', 'NS5', 'm'),
    ('6.cum_m_queries', 'NS6', 'c'),
    )
#    (filename, label, style)

def plot():
    plots = []
    xs = []
    for line_to_plot in lines_to_plot:
        filename, label, style = line_to_plot
        x = []
        y = []
        for line in open(filename):
            ts, num_queries = line.split()
            x.append(int(ts))
            y.append(int(num_queries))
            pylab.plot(x, y, style, label=label)

pylab.legend(loc='upper left')
pylab.savefig(output_filename)

print 'Output saved to:', output_filename
