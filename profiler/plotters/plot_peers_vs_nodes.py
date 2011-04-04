import pylab

pylab.title('# peers VS # nodes returning values')
pylab.xlabel('Number of nodes returning values')
pylab.ylabel('Number of unique peers)')

output_filename = 'plots/peers_vs_nodes.eps'

lines_to_plot = (
    ('8.l_num_peers', '', 'k,'),
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
            str_peers = line.split()
            num_peers = sum([int(ps) for ps in str_peers])
            num_nodes = len(str_peers)
            x.append(num_nodes)
            y.append(num_peers)
        pylab.loglog(x, y, style, label=label)
        #pylab.axis([0, 1500, 0, 10])


    pylab.legend()#loc='upper left')
    pylab.savefig(output_filename)
#    pylab.close()
    

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()
