*************
pymdht 11.8.3
*************
aka "NS\8\3" (message label)

NOTE on version number.
We use the following version format:
 - first number: release year (two digits)
 - second number: release month number
 - third number: sub-release number, even numbers indicate stable release, odd
numbers indicate development (unstable)

Examples:
 - 11.8.0 Code released in Aug 2011 (stable release)
 - 11.8.1 Development code right after 11.8.0 release (unstable)
 - 11.8.2 Bugfix release (stable release)


AUTHORS
=======

Raul Jimenez
Flutra Osmani
Ismael Saad Garcia (lookup experiments)
Sara Dar (MDHT visualization)
Shariq Mobeen (GUI + lookup visualization)
S.M. Sarwarul Islam Rizvi (lookup experiments)
Zinat Sultana (routing table extraction experiments)


ORGANIZATION

The code is organized as follows:

* Directories:
  - core
    Core modules of the Pymdht package. The 'pymdht.py' file contains the
    package's API.
  - doc
    Documentation.
  - geo
    Modules related to geo-location services (not used by default).
  - plugins
    Modules providing lookup implementation (lookup_*.py files) and
    routing table management (routing_*.py files).
  - profiler
    Toolkit capable to launch several MDHT nodes (conductor.py), parse
    network captures (parser.py), and plot graphs from parsing results
    (plotter.py). More information in profiler/README.txt
  - ui
    User interface (text and graphical)

* Files:
  - CHANGES.txt, LGPL-2.1.txt, LICENSE.txt, README.txt
    Standard (auto explicative) names.
  - MANIFEST.in, setup.py
    Standard Python distribution files
  - interactive_dht.py
    Simple  example of how the Pymdht can be used. Use '--help' to get a list
    of available command line options.


INSTALLATION

This package uses Python 2.5 standard library. No extra modules need to be
installed.

A Makefile is provided to run the tests. The tests require the nose test
framework to work.


API

The API is located in core/pymdht.py. This is the only module necessary
to use the package.

Users should ONLY use the methods provided in core/pymdht.py.

Users can additionally use the Id and Node classes as they wish. These classes aqre
located in core/identifier.py and core/node.py

ipython is useful to try out functionality and/or debug.


TESTS

Just run 'make'. see core/Makefile for details.

In order to run the tests you need the following packages (ubuntu):
python-nose 
python-coverage (optional but very recommended)


PROFILING

In order to do profiling you need the following packages (ubuntu):

python-profiler
kcachegrind (profile viewer)

and from easy_install (comes with the python-setuptools package in Ubuntu):
profilestats (produces input for both RunSnakeRun and KCachegrind)
runsnakerun (simple and nice profile viewer)


PYMDHT DAEMON (unsupported)

This daemon serves as a simple interface between swift transport
protocol and pymdht.  It takes takes inhohashes from swift as input,
uses pymdht to find peers for the corresponding infohashes, and
finally returns the list of peers (in bursts, as they are discovered)
to the swift core. 

To run pymdht daemon:
- pymdht_daemon.py
- refer to pymdht_daemon_api.txt for technical details


GEO SCORING API (unsupported)

Module geo.py contains a set of functions that can be used to retrieve peer's
location-related information, such as: city, country, latitude,
longitude etc (based on the geoip library). In addition, this module
contains functions to calculate coordinate distances between two
peers, find if peers are in the same country, and score peers
according to a defined (in geo.py) metric.
 
Geo scoring is not enabled by default, when running pymdht daemon. It can
be switched on this way:

- python pymdht_daemon.py --geoip

For geo module to work (only if running geo scoring), you need to
install the following libraries (Ubuntu):
1. python-geoip
2. geoip-database
3. libgeoip1
4. Run geolitecityupdate.sh script to get the latest version of the
city database. The data, otherwise, is located here: "/usr/share/GeoIP/GeoIPCity.dat"


CLEAN CODE

In order to check "code quality" you need the following packages:
pylint (e.g. pylint --errors-only *.py >errors)

EDITING

In case it's useful to you. I use this Emacs configuration:
https://github.com/rauljim/emacs


