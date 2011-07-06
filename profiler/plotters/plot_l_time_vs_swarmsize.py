import pylab
import sys

sys.path.append('..')
import parsers.cdf as cdf

pylab.title('Lookup Time VS Swarm Size')
pylab.xlabel('Lookup Time T1 (s)')
pylab.ylabel('CDF')

output_filename = 'plots/cdf_l_time_vs_swarmsize.eps'

lines_to_plot = (
#    ('0.l_time', '0.l_swarm_size', 'UT', '+'),
    ('10.l_time', '10.l_swarm_size', '10', 'k-'),
    ('0.l_time', '0.l_swarm_size', '0', 'g:'),
    )
#    (filename, label, style)

swarmsize_lines = (
    (50, '<50', '+'),
    (100, '50-100', 'v'),
    (200, '100-200', 'x'),
    (9999999, '>200', '^'),
    )
markevery = 100

def plot():
    for time_filename, size_filename, f_label, f_style in lines_to_plot:
        time_file = open('parser_results/' + time_filename)
        size_file = open('parser_results/' + size_filename)
        times = {}
        for mark, _, _ in swarmsize_lines:
            times[mark] = []
        for line in time_file:
            time = float(line.split()[0])
            size = int(size_file.next().split()[0])
            for mark, _, _ in swarmsize_lines:
                if size <= mark:
                    times[mark].append(time)
                    break
        for mark, m_label, m_style in reversed(swarmsize_lines):
            cum_values = cdf.cdf(times[mark])            
            x = [cum_value[1] for cum_value in cum_values]
            y = [cum_value[0] for cum_value in cum_values]
            pylab.semilogx(x, y, f_style+m_style,
                           label=f_label+' '+m_label,
                           markevery=markevery)
    pylab.legend(loc='lower right')
    pylab.savefig(output_filename)
#    pylab.close()
    

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()
