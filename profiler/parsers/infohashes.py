# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""

"""

from parser_utils import openf
import core.message as message


class Parser(object):

    def __init__(self, my_ip):
        self.my_ip = my_ip

        self.cum_in_file = openf('m.cum_in', 'w')
        self.cum_out_file = openf('m.cum_out', 'w')
        self.cum_in = 0
        self.cum_out = 0
        self.sec_in_file = openf('m.sec_in', 'w')
        self.sec_out_file = openf('m.sec_out', 'w')
        self.sec_in = 0
        self.sec_out = 0

        self.cum_q_in_file = openf('m.cum_q_in', 'w')
        self.cum_q_out_file = openf('m.cum_q_out', 'w')
        self.cum_q_in = 0
        self.cum_q_out = 0
        self.sec_q_in_file = openf('m.sec_q_in', 'w')
        self.sec_q_out_file = openf('m.sec_q_out', 'w')
        self.sec_q_in = 0
        self.sec_q_out = 0

        self.cum_r_in_file = openf('m.cum_r_in', 'w')
        self.cum_r_out_file = openf('m.cum_r_out', 'w')
        self.cum_r_in = 0
        self.cum_r_out = 0
        self.sec_r_in_file = openf('m.sec_r_in', 'w')
        self.sec_r_out_file = openf('m.sec_r_out', 'w')
        self.sec_r_in = 0
        self.sec_r_out = 0

        self.current_sec = 0
        self.last_write = 0

        self.versions = {}
        self.ips = set()

        self.announce_ips = set()

        self.num_announces = {}
        self.num_same_port = {}

        self.getpeers_infohashes = set()
        self.announced_infohashes = set()
        self.total_infohashes = set()
        self.last_ts = 0
        self.last_total = 0

    def _write(self, ts):
        int_ts = int(ts)
        if int_ts > self.current_sec:
            self.cum_in_file.write('%d\t%d\n' % (self.current_sec,
                                                  self.cum_in))
            self.cum_out_file.write('%d\t%d\n' % (self.current_sec,
                                                  self.cum_out))
            self.sec_in_file.write('%d\t%d\n' % (self.current_sec,
                                                  self.sec_in))
            self.sec_out_file.write('%d\t%d\n' % (self.current_sec,
                                                  self.sec_out))
            self.cum_q_in_file.write('%d\t%d\n' % (self.current_sec,
                                                  self.cum_q_in))
            self.cum_q_out_file.write('%d\t%d\n' % (self.current_sec,
                                                  self.cum_q_out))
            self.sec_q_in_file.write('%d\t%d\n' % (self.current_sec,
                                                  self.sec_q_in))
            self.sec_q_out_file.write('%d\t%d\n' % (self.current_sec,
                                                  self.sec_q_out))
            self.cum_r_in_file.write('%d\t%d\n' % (self.current_sec,
                                                  self.cum_r_in))
            self.cum_r_out_file.write('%d\t%d\n' % (self.current_sec,
                                                  self.cum_r_out))
            self.sec_r_in_file.write('%d\t%d\n' % (self.current_sec,
                                                  self.sec_r_in))
            self.sec_r_out_file.write('%d\t%d\n' % (self.current_sec,
                                                  self.sec_r_out))
            for i in xrange(self.current_sec + 1, int_ts):
                self.sec_in_file.write('%d\t%d\n' % (i, 0))
                self.sec_out_file.write('%d\t%d\n' % (i, 0))
                self.sec_q_in_file.write('%d\t%d\n' % (i, 0))
                self.sec_q_out_file.write('%d\t%d\n' % (i, 0))
                self.sec_r_in_file.write('%d\t%d\n' % (i, 0))
                self.sec_r_out_file.write('%d\t%d\n' % (i, 0))
            self.current_sec = int_ts
            self.sec_in = 0
            self.sec_out = 0
            self.sec_q_in = 0
            self.sec_q_out = 0
            self.sec_r_in = 0
            self.sec_r_out = 0

    def _parse_version(self, addr, msg):
        ip = addr[0]
        if msg.version:
            v = msg.version[:2]
        else:
            v = '--'
        if ip not in self.ips:
            self.ips.add(ip)
            self.versions[v] = self.versions.get(v, 0) + 1
        return v
            
        
    def outgoing_msg(self, ts, dst_addr, msg):
        return
        self._write(ts)
        self.cum_out += 1
        self.sec_out += 1
        if msg.type == message.QUERY:
            self.cum_q_out += 1
            self.sec_q_out += 1
        elif msg.type == message.RESPONSE:
            self.cum_r_out += 1
            self.sec_r_out += 1


    def incoming_msg(self, ts, src_addr, msg):
        if (msg.type == message.QUERY
            and msg.query == message.ANNOUNCE_PEER):
            self.announced_infohashes.add(msg.info_hash)
            self.total_infohashes.add(msg.info_hash)
        if (msg.type == message.QUERY
            and msg.query == message.GET_PEERS):
            self.getpeers_infohashes.add(msg.info_hash) 
            self.total_infohashes.add(msg.info_hash)
        if ts > self.last_ts + 60:
            self.last_ts = ts
            delta = len(self.total_infohashes) - self.last_total
            self.last_total = len(self.total_infohashes)
            print ts, len(self.getpeers_infohashes),
            print len(self.announced_infohashes),
            print len(self.total_infohashes),
            print delta
            return
            
            self.announce_ips.add(src_addr[0])
            v = self._parse_version(src_addr, msg)
            same_port = msg.bt_port == src_addr[1]
            if same_port:
                self.num_same_port[v] = self.num_same_port.get(v, 0) + 1
            self.num_announces[v] = self.num_announces.get(v, 0) + 1
            if 0:#len(self.announce_ips) % 1000 == 0:
                total_announces = 0
                total_same_port = 0
                for v in self.num_announces.keys():
                    num_announces = self.num_announces[v]
                    num_same_port = self.num_same_port.get(v, 0)
                    total_announces += num_announces
                    total_same_port += num_same_port
                    print v, num_announces,
                    print 100. * num_same_port / num_announces
                print 'TOTAL', total_announces,
                print 100. * total_same_port / total_announces
                        
        return
        self._write(ts)
        self.cum_in += 1
        self.sec_in += 1
        if msg.type == message.QUERY:
            self.cum_q_in += 1
            self.sec_q_in += 1
        elif msg.type == message.RESPONSE:
            self.cum_r_in += 1
            self.sec_r_in += 1


    def done(self):
        num_ips = float(len(self.ips))
        v_file = openf('m.versions', 'w')
        v_file.write('%s\t%d\t%f\n' % ('ALL', num_ips, 1))
        for v, num_hits in self.versions.iteritems():
            v_file.write('%s\t%d\t%f\n' % (v, num_hits, num_hits/num_ips))
