import pylab

pylab.title('Number of GET_PEERS and ANNOUNCE_PEER VS Time(per_minute)')
pylab.xlabel('time(in Minutes)')
pylab.ylabel('Number of GET_PEERS and ANNOUNCE _PEER message (s)')

output_filename = 'plots/get_peers_announce_peer_vs_per_minute.eps'

lines_to_plot = (    
    ('2.per_min_gp', 'GET_PEERS', 'r'),
    ('2.per_min_announce_peer', 'ANNOUNCE_PEER', 'b'),       
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
            data = line.split()
            time = data[0]
            num_gp = data[1]
            #x.append(time_min)
            #y.append(num_gp)
            x.append(int(time))
            y.append(int(num_gp))
        pylab.semilogy(x, y, style, label=label)
        
        #pylab.axis([0, 1500, 0, 10])


    pylab.legend(loc='upper left')
    pylab.savefig(output_filename)
#    pylab.close()
    

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()