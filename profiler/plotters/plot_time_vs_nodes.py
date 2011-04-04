import pylab

pylab.title('Lookup Time VS # nodes returning values')
pylab.xlabel('Number of nodes returning values')
pylab.ylabel('Lookup Time (s)')

output_filename = 'plots/l_time_vs_nodes.eps'

lines_to_plot = (
    ('0.l_peers_time', '0', 'y+'),
    ('10.l_peers_time', '10', 'k.'),
    )
#    (filename, label, style)

def plot():
    plots = []
    xs = []
    for filename, label, style in lines_to_plot:
        x = []
        y = []
        f = open('parser_results/' + filename)
        for line in f:
            str_times = line.split()
            t1 = float(str_times[0])
            num_nodes = len(str_times)
            x.append(num_nodes)
            y.append(t1)
        pylab.semilogy(x, y, style, label=label)
        #pylab.axis([0, 1500, 0, 10])


    pylab.legend()#loc='upper left')
    pylab.savefig(output_filename)
#    pylab.close()
    

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()
