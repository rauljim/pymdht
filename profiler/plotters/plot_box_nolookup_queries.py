import pylab

pylab.title('Lookup Queries')
pylab.xlabel('Client')
pylab.ylabel('Lookup queries')

boxes_to_plot = (
    ('ns.nolookup_queries', 'ut-50', 'ks-'),
    ('ut.nolookup_queries', 'ut-50', 'ks-'),
    ('ut-50.nolookup_queries', 'ut-50', 'ks-'),
    #('test1', 'l1', 'rs-'),
    #('test2', 'l2', 'bs-'),
    )
#    (filename, label, style)


plots = []
xs = []
for box_to_plot in boxes_to_plot:
    filename, label, style = box_to_plot
    xs.append([float(line) for line in open(filename)])
boxplot = pylab.boxplot(xs)
pylab.setp(pylab.gca(), 'xticklabels', ('NS', 'UT', 'UT-50'))

#    plots.append(boxplot)

#pylab.figlegend(plots, ('CC'), loc='lower right')
pylab.show()

