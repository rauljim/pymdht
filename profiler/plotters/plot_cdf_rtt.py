import pylab

pylab.title('RTT')
pylab.xlabel('Time (s)')
pylab.ylabel('CDF')

output_filename = 'plots/cdf_rtt.eps'

lines_to_plot = (
    ('m.t_rtt.cdf', 'RTT', 'k'),
    )

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
