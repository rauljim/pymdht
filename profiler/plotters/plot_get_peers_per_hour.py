import pylab

pylab.title('Number of GET_PEERS VS Time(per_hour)')
pylab.xlabel('time(in Hour)')
pylab.ylabel('Number of GET_PEERS message (s)')

output_filename = 'plots/get_peers_vs_per_hour.eps'

lines_to_plot = (
    ('0.per_hour_gp', '0', 'r'),
    ('1.per_hour_gp', '1', 'k'),
    ('2.per_hour_gp', '2', 'b'),
    ('3.per_hour_gp', '3', 'g'),
    ('4.per_hour_gp', '4', 'y'),
    ('5.per_hour_gp', '5', 'm'),
    ('6.per_hour_gp', '6', 'k:'),
    ('7.per_hour_gp', '7', 'b:'),
    ('8.per_hour_gp', '8', 'y:'),
    ('9.per_hour_gp', '9', 'm:'),
    
    )

def plot():
    plots = []
    xs = []
    for filename, label, style in lines_to_plot:
        x = []
        y = []
	i = i + 1
        f = open('parser_results/' + filename)
        for line in f:
            data = line.split()
            time = i
            num_gp = line
            x.append(int(time))
            y.append(int(num_gp))
	    i = i + 1
        pylab.plot(x, y, style, label=label)
        
    pylab.legend(loc='upper left')
    pylab.savefig(output_filename)
#    pylab.close()
    

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()
