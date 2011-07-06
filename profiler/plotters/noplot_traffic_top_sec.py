# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information



def get_top10(sec_file):
    top10 = []
    for line in sec_file:
        num_packets = int(line.split()[1])
        i = min(len(top10), 10)
        while i > 0 and num_packets > top10[i-1]:
            i -= 1
        if i < 10:
            top10[i:i] = [num_packets]
    return top10[:10]

if __name__ == '__main__':
    
    sec_in_file = open('parser_results/m.sec_in')
    top10 = get_top10(sec_in_file)
    print 'Packets sent (busiest seconds): %r' % (top10)
    sec_in_file.close()
    sec_out_file = open('parser_results/m.sec_out')
    top10 = get_top10(sec_out_file)
    print 'Packets received (busiest seconds): %r' % (top10)
    sec_out_file.close()

