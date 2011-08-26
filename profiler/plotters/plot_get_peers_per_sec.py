import pylab

pylab.title('Number of GET_PEERS VS Time(per_second)')
pylab.xlabel('time(in Second)')
pylab.ylabel('Number of GET_PEERS message (s)')

output_filename = 'plots/get_peers_vs_per_second.eps'

lines_to_plot = (
    ('0.per_sec_gp', '0', 'r'),
    ('1.per_sec_gp', '1', 'k'),
    ('2.per_sec_gp', '2', 'b'),
    ('3.per_sec_gp', '3', 'g'),
    ('4.per_sec_gp', '4', 'y'),
    ('5.per_sec_gp', '5', 'm'),
    ('6.per_sec_gp', '6', 'k:'),
    ('7.per_sec_gp', '7', 'b:'),
    ('8.per_sec_gp', '8', 'y:'),
    ('9.per_sec_gp', '9', 'm:'),
    
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