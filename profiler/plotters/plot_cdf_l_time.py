import pylab

pylab.title('Lookup time (any node)')
pylab.xlabel('Time (s)')
pylab.ylabel('CDF')

output_filename = 'plots/cdf_l_time.eps'

lines_to_plot = (
    ('0.l_time.cdf', '0', 'r'),
    ('1.l_time.cdf', '1', 'g:+'),
    ('2.l_time.cdf', '2', 'g:v'),
    ('3.l_time.cdf', '3', 'g:x'),
#    ('4.l_time.cdf', '4', 'y., 1'),
    ('5.l_time.cdf', '5', 'g:^'),
    ('6.l_time.cdf', '6', 'k-+'),
    ('7.l_time.cdf', '7', 'k-v'),
    ('8.l_time.cdf', '8', 'k-x'),
#    ('9.l_time.cdf', '9', 'k.', 2),
    ('10.l_time.cdf', '10', 'k-^'),
    )
#    (filename, label, style)

def plot():
    markevery = 300
    for filename, label, style in lines_to_plot:
        x = []
        y = []
        for line in open('parser_results/' + filename):
            splitted_line = line.split()
            if not splitted_line:
                continue
            cum = float(splitted_line[0])
            value = float(splitted_line[1])
            y.append(cum)
            x.append(value)
        pylab.semilogx(x, y, style, label=label, markevery=markevery)
#        markevery+=15

    pylab.legend(loc='lower right')
    pylab.savefig(output_filename)

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()
