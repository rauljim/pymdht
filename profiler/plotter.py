#! /usr/bin/python

import os

plot_scripts = [
    #'plot_get_peers_per_min.py',
    #'plot_get_peers_per_hour.py',
    #'plot_find_node_per_min.py',
    #'plot_find_node_per_hour.py',
    'plot_announce_per_min.py',
    #'plot_announce_per_hour.py',
    #'plot_ping_per_min.py',
    #'plot_ping_per_hour.py',
    #'plot_node2_get_peers_announce_per_min.py',
    ]

if __name__ == '__main__':
    try:
        os.mkdir('plots')
    except (OSError):
        pass
    for plot_script in plot_scripts:
        os.system('python plotters/' + plot_script)
