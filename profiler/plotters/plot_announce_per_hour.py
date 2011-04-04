import pylab

pylab.title('Number of ANNOUNCE VS Time(per_hour)')
pylab.xlabel('time(in Hour)')
pylab.ylabel('Number of ANNOUNCE message (s)')

output_filename = 'plots/announce_vs_per_hour.eps'

lines_to_plot = (
    ('0.per_hour_announce_peer', '0', 'r'),
    ('1.per_hour_announce_peer', '1', 'k'),
    ('2.per_hour_announce_peer', '2', 'b'),
    ('3.per_hour_announce_peer', '3', 'g'),
    ('4.per_hour_announce_peer', '4', 'y'),
    ('5.per_hour_announce_peer', '5', 'm'),
    ('6.per_hour_announce_peer', '6', 'k:'),
    ('7.per_hour_announce_peer', '7', 'b:'),
    ('8.per_hour_announce_peer', '8', 'y:'),
    ('9.per_hour_announce_peer', '9', 'm:'),
    
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
            num_announce = data[1]
            #x.append(time_min)
            #y.append(num_gp)
            x.append(int(time))
            y.append(int(num_announce))
        pylab.semilogy(x, y, style, label=label)
        
        #pylab.axis([0, 1500, 0, 10])


    pylab.legend(loc='upper left')
    pylab.savefig(output_filename)
#    pylab.close()
    

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()