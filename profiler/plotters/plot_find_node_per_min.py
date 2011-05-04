import pylab

pylab.title('Number of FIND_NODE VS Time(per_min)')
pylab.xlabel('time(in Minute)')
pylab.ylabel('Number of FIND_NODE message (s)')

output_filename = 'plots/find_node_vs_per_min.eps'

lines_to_plot = (
    ('0.per_min_find_node', '0', 'r'),
    ('1.per_min_find_node', '1', 'k'),
    ('2.per_min_find_node', '2', 'b'),
    ('3.per_min_find_node', '3', 'g'),
    ('4.per_min_find_node', '4', 'y'),
    ('5.per_min_find_node', '5', 'm'),
    ('6.per_min_find_node', '6', 'k:'),
    ('7.per_min_find_node', '7', 'b:'),
    ('8.per_min_find_node', '8', 'y:'),
    ('9.per_min_find_node', '9', 'm:'),
    
    )
#    (filename, label, style)

def plot():
    plots = []
    xs = []
    for filename, label, style in lines_to_plot:
        x = []
        y = []
	i = i + 1
        f = open('parser_results/' + filename)
        for line in f:
            #data = line.split()
            time = i
            num_fn = line
            x.append(int(time))
            y.append(int(num_fn))
	    i = i + 1
        pylab.plot(x, y, style, label=label)
        
        #pylab.axis([0, 1500, 0, 10])


    pylab.legend(loc='upper left')
    pylab.savefig(output_filename)
#    pylab.close()
    

    print 'Output saved to:', output_filename

if __name__ == '__main__':
    plot()
