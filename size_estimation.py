from core.identifier import Id


for line in open('size_estimation.dat'):
    ids = [Id(hexid) for hexid in line.split()]
    log_distances = [ids[0].log_distance(ids[1]),
                     ids[0].log_distance(ids[2]),
                     ids[1].log_distance(ids[2]),
                     ]

    avg = (sum(log_distances) - max(log_distances)) / 2.
    size = pow(2, 160-avg) /1000000.
    
    print log_distances, avg, '%.2f M' % size
    
