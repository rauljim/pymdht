import pylab

pylab.title('Number of ANNOUNCE VS Time(per_minute)')
pylab.xlabel('time(in Minutes)')
pylab.ylabel('Number of ANNOUNCE message (s)')

output_filename = 'plots/announce_vs_per_minute.eps'

lines_to_plot = (
    ('0.per_min_announce_peer', '0', 'r'),
    ('1.per_min_announce_peer', '1', 'k'),
    ('2.per_min_announce_peer', '2', 'b'),
    ('3.per_min_announce_peer', '3', 'g'),
    ('4.per_min_announce_peer', '4', 'y'),
    ('5.per_min_announce_peer', '5', 'm'),
    ('6.per_min_announce_peer', '6', 'k:'),
    ('7.per_min_announce_peer', '7', 'b:'),
    ('8.per_min_announce_peer', '8', 'y:'),
    ('9.per_min_announce_peer', '9', 'm:'),
    
    )
#    (filename, label, style)

def plot():
    plots = []
    for filename, label, style in lines_to_plot:
        x = []
        y = []
	i = 0
        f = open('parser_results/' + filename)
        for line in f:
            #data = line.split()
            time = i
            num_announce = line
            x.append(int(time))
            y.append(int(num_announce))
	    i = i + 1
        pylab.plot(x, y, style, label=label)

    pylab.legend(loc='upper left')
    pylab.savefig(output_filename)
#    pylab.close()
    

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()
