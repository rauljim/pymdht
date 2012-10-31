# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import unittest

import ptime as time
import bootstrap

import logging, logging_conf

logging_conf.testing_setup(__name__)
logger = logging.getLogger('dht')

STABLE_ADDR = ('192.16.127.98', 7000)
RANDOM_ADDR = ('127.11.1.1', 578)
SAME_SUBNET_ADDR = ('127.11.1.2', 5718)
RANDOM_ADDR2 = ('127.12.1.1', 3708)

CONF_PATH = 'test_logs'

class TestBootstrap(unittest.TestCase):

    def setUp(self):
        time.mock_mode()

    def test_general(self):
        b = bootstrap.OverlayBootstrapper(CONF_PATH, False)
        self.assertEqual(len(b.get_sample_unstable_addrs(5)), 5)
        assert RANDOM_ADDR not in b.get_sample_unstable_addrs(2)
        assert STABLE_ADDR in b.get_shuffled_stable_addrs()
        assert RANDOM_ADDR not in b.get_shuffled_stable_addrs()

    def test_report_short(self):
        b = bootstrap.OverlayBootstrapper(CONF_PATH, False)
        initial_unstable_len = b.unstable_len
        b.report_reachable(RANDOM_ADDR, 0)
        # This addr should be added to the list
        assert b.unstable_len == initial_unstable_len + 1
        assert RANDOM_ADDR in b.get_sample_unstable_addrs(b.unstable_len)
        assert not b.is_hardcoded(RANDOM_ADDR)

        b.report_unreachable(RANDOM_ADDR)
        assert b.unstable_len == initial_unstable_len
        assert RANDOM_ADDR not in b.get_sample_unstable_addrs(b.unstable_len)
        assert not b.is_hardcoded(RANDOM_ADDR)

    def test_report_unreachable(self):
        b = bootstrap.OverlayBootstrapper(CONF_PATH, False)
        initial_unstable_len = b.unstable_len

        addrs = b.get_sample_unstable_addrs(50)
        # Off-line mode ON, addrs are NOT removed
        b.report_unreachable(addrs[0])
        assert b.unstable_len == initial_unstable_len
        assert b.is_hardcoded(addrs[0])
        # Off-line mode ON, addrs are NOT removed
        b.report_unreachable(addrs[1])
        assert b.unstable_len == initial_unstable_len
        assert b.is_hardcoded(addrs[1])
        # Off-line mode OFF, addrs ARE removed
        b.report_unreachable(addrs[6])
        assert b.unstable_len == initial_unstable_len - 1
        assert b.is_hardcoded(addrs[6])
        # Off-line mode OFF, addrs ARE removed.
        b.report_unreachable(addrs[3])
        assert b.unstable_len == initial_unstable_len - 2
        assert b.is_hardcoded(addrs[3])

        assert addrs[0] in b.get_sample_unstable_addrs(b.unstable_len)
        assert addrs[1] in b.get_sample_unstable_addrs(b.unstable_len)
        assert addrs[6] not in b.get_sample_unstable_addrs(b.unstable_len)
        assert addrs[3] not in b.get_sample_unstable_addrs(b.unstable_len)

        # Reporting a non-bootstrap addr has no effect
        assert b.unstable_len == initial_unstable_len - 2
        assert RANDOM_ADDR not in b.get_sample_unstable_addrs(b.unstable_len)
        b.report_unreachable(RANDOM_ADDR)
        assert b.unstable_len == initial_unstable_len - 2
        assert RANDOM_ADDR not in b.get_sample_unstable_addrs(b.unstable_len)
        
    def test_report_short(self):
        b = bootstrap.OverlayBootstrapper(CONF_PATH, False)
        initial_unstable_len = b.unstable_len

        b.report_reachable(RANDOM_ADDR)
        # Addr is added right away
        assert b.unstable_len == initial_unstable_len + 1
        assert RANDOM_ADDR in b.get_sample_unstable_addrs(b.unstable_len)

        b.report_reachable(SAME_SUBNET_ADDR)
        # Just one IP per subnet
        assert b.unstable_len == initial_unstable_len + 1
        assert SAME_SUBNET_ADDR not in b.get_sample_unstable_addrs(b.unstable_len)

        b.report_reachable(RANDOM_ADDR2)
        # Addr is added right away
        assert b.unstable_len == initial_unstable_len + 2
        assert RANDOM_ADDR2 in b.get_sample_unstable_addrs(b.unstable_len)

    def test_report_long(self):
        b = bootstrap.OverlayBootstrapper(CONF_PATH, False)
        initial_unstable_len = b.unstable_len

        b.report_reachable(RANDOM_ADDR, 1)
        # Addr's uptime is too short
        assert b.unstable_len == initial_unstable_len
        assert RANDOM_ADDR not in b.get_sample_unstable_addrs(b.unstable_len)

        b.report_reachable(RANDOM_ADDR, bootstrap.MIN_LONG_UPTIME)
        # Addr is added right away
        assert b.unstable_len == initial_unstable_len + 1
        assert RANDOM_ADDR in b.get_sample_unstable_addrs(b.unstable_len)

        b.report_reachable(RANDOM_ADDR2, bootstrap.MIN_LONG_UPTIME)
        # Just one addr per hour
        assert b.unstable_len == initial_unstable_len + 1
        assert RANDOM_ADDR2 not in b.get_sample_unstable_addrs(b.unstable_len)

        time.sleep(bootstrap.ADD_LONG_UPTIME_ADDR_EACH)
        b.report_reachable(RANDOM_ADDR2, bootstrap.MIN_LONG_UPTIME)
        # Addr is added now (after the sleep)
        assert b.unstable_len == initial_unstable_len + 2
        assert RANDOM_ADDR2 in b.get_sample_unstable_addrs(b.unstable_len)

    def tearDown(self):
        time.normal_mode()


if __name__ == '__main__':
    unittest.main()
