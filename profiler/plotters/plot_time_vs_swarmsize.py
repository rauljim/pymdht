import pylab

pylab.title('Lookup Time VS Swarm Size')
pylab.xlabel('Swarm size (unique peers)')
pylab.ylabel('Lookup Time (s)')

output_filename = 'l_time_vs_swarmsize.eps'

lines_to_plot = (
    ('0.l_time', '0.l_swarm_size', 'UT', '+'),
    ('6.l_time', '6.l_swarm_size', 'NS6', '*'),
    )
#    (filename, label, style)

def plot():
    plots = []
    xs = []
    for time_filename, size_filename, label, style in lines_to_plot:
        x = []
        y = []
        time_file = open(time_filename)
        size_file = open(size_filename)
        for line in time_file:
            time = float(line.split()[0])
            size = int(size_file.next().split()[0])
            x.append(size)
            y.append(time)
        pylab.semilogx(x, y, style, label=label)
        #pylab.axis([0, 1500, 0, 10])


    pylab.legend()#loc='upper left')
    pylab.savefig(output_filename)
#    pylab.close()
    

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()
