import pylab

pylab.title('Lookup time')
pylab.xlabel('Time (s)')
pylab.ylabel('CDF')

output_filename = 'cdf_l_time.eps'

lines_to_plot = (
    ('0.l_time.cdf', 'UT', 'k'),
    ('1.l_time.cdf', 'NS1', 'r:'),
    ('2.l_time.cdf', 'NS2', 'b:'),
    ('3.l_time.cdf', 'NS3', 'g:'),
    ('4.l_time.cdf', 'NS4', 'y:'),
    ('5.l_time.cdf', 'NS5', 'c:'),
    ('6.l_time.cdf', 'NS6', 'r-'),
    ('7.l_time.cdf', 'NS7', 'b-'),
    ('8.l_time.cdf', 'NS8', 'g'),
#    ('9.l_time.cdf', 'NS9', 'y'),
    )
#    (filename, label, style)

def plot():
    for filename, label, style in lines_to_plot:
        x = []
        y = []
        for line in open(filename):
            splitted_line = line.split()
            if not splitted_line:
                continue
            cum = float(splitted_line[0])
            value = float(splitted_line[1])
            y.append(cum)
            x.append(value)
        pylab.semilogx(x, y, style, label=label)

    pylab.legend(loc='lower right')
    pylab.savefig(output_filename)

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()
