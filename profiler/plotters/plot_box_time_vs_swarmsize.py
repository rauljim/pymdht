import pylab

pylab.title('Lookup Time VS Swarm Size (NS6)')
pylab.xlabel('Swarm size (unique peers)')
pylab.ylabel('Lookup Time (s)')

output_filename = 'plots/box_l_time_vs_swarmsize.eps'

lines_to_plot = (
#    ('0.l_time', '0.l_swarm_size', 'UT', '+'),
    ('6.l_time', '6.l_swarm_size', 'NS6', '*'),
    )
#    (filename, label, style)

def plot():
    swarmsize_marks = [20, 50, 100, 200]
    times = {}
    for mark in swarmsize_marks:
        times[mark] = []
    for time_filename, size_filename, label, style in lines_to_plot:
        time_file = open('parser_results/' + time_filename)
        size_file = open('parser_results/' + size_filename)
        for line in time_file:
            time = float(line.split()[0])
            size = int(size_file.next().split()[0])
            for mark in swarmsize_marks:
                if size <= mark:
                    times[mark].append(time)
                    break
    xs = []
    labels = []
    for mark in swarmsize_marks:
        xs.append(times[mark])
        labels.append('<=%d' % mark)
    pylab.boxplot(xs)
    pylab.setp(pylab.gca(), 'xticklabels', labels)
    pylab.savefig(output_filename)
#    pylab.close()
    

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()
