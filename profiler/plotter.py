#! /usr/bin/python

import os

plot_scripts = [
    'plot_l_time_vs_swarmsize.py',
    'plot_cum_m_queries.py',
    'plot_cdf_l_queries.py',
    'plot_cdf_l_time.py',
    'plot_cdf_l_time_auth.py',
    'plot_cdf_l_time_closest.py',
    'plot_box_l_time.py',
    'plot_box_l_time_nofliers.py',
    'plot_box_l_queries.py',
    'plot_time_vs_swarmsize.py',
    'plot_box_time_vs_swarmsize.py',
    'noplot_traffic_top_sec.py',
    ]


if __name__ == '__main__':
    try:
        os.mkdir('plots')
    except (OSError):
        pass
    for plot_script in plot_scripts:
        os.system('python plotters/' + plot_script)
