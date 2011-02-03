from core.identifier import Id


MAX_LOG_DISTANCE = 140
PARTIAL = 60

multiplier = pow(2, 160 - MAX_LOG_DISTANCE - 1)

def print_estimation(num_responses_list):
    avg = float(sum(num_responses_list)) / len(num_responses_list)
    size = multiplier * avg / 1000000
    print 'Estimation: %.2f M' % (
            size)
    




partial_num_responses = []
total_num_responses = []

for i, line in enumerate(open('size_estimation.dat')):
    try:
        num_queries, num_responses = [int(x) for x in line.split()]
    except:
        break
    partial_num_responses.append(num_responses)
    total_num_responses.append(num_responses)
    if i % PARTIAL == 0:
        print_estimation(partial_num_responses)
        partial_num_responses = []

print len(partial_num_responses),
print_estimation(partial_num_responses)
        
print 'Final', 
print_estimation(total_num_responses)
