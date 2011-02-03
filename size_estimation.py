from core.identifier import Id

sizes = []

for line in open('size_estimation.dat'):
    try:
        num_queries, num_responses = [int(x) for x in line.split()]
    except:
        break
    size = pow(2, 19) * num_responses / 1000000.
    print '%d queries, %d responses. Estimation: %.2f M' % (
        num_queries,
        num_responses,
        size)
    sizes.append(size)

        
avg = sum(sizes)/len(sizes)
print 'Final estimation: %.2f M' % avg
