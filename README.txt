pymdht 1.0.1-M36-tribler

INSTALLATION

This package uses Python 2.5 standard library. No extra modules need to be
installed.

A Makefile is provided to run the tests. The tests require the nose test
framework to work.

API

The API is located in pymdht.py. This is the only module necessary to use the
package.

Users must ONLY use the methods provided in pymdht.py.

Users can use the Id and Node containers as they wish. These classes are
located in identifier.py and node.py

EXAMPLES

Two examples are provided in the distribution:

- server_dht.py

Do the routing maintainance tasks plus a get_peers lookup to a random
identifier every 10 minutes.

- interactive_dht.py

Do the routing maintainance task plus get_peers lookups asked by the user
during the interactive session.

TESTS

In order to run the tests you need the following packages (ubuntu):
python-nose 
python-coverage (optional but very recommended)

PROFILING

In order to do profiling you need tht following packages (ubuntu):

python-profiler
kcachegrind (profile viewer)

and from easy_install (comes with the python-setuptools package in Ubuntu):
profilestats (produces input for both RunSnakeRun and KCachegrind)
runsnakerun (simple and nice profile viewer)


PYMDHT DAEMON

This daemon serves as a simple interface between swift transport
protocol and pymdht.  It takes takes inhohashes from swift as input,
uses pymdht to find peers for the corresponding infohashes, and
finally returns the list of peers (in bursts, as they are discovered)
to the swift core. 

To run pymdht daemon:
- pymdht_daemon.py
- refer to pymdht_daemon_api.txt for technical details

GEO SCORING API

Module geo.py contains a set of functions that can be used to retrieve peer's
location-related information, such as: city, country, latitude,
longitude etc (based on the geoip library). In addition, this module
contains functions to calculate coordinate distances between two
peers, find if peers are in the same country, and score peers
according to a defined (in geo.py) metric.
 
Geo scoring is enabled by default, when running pymdht daemon. It can
be switched off this way:

- python pymdht_daemon.py --no-geoip

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

In case it's useful to you. I use this Emacs configuration (with minor
modifications):

http://09-f9-11-02-9d-74-e3-5b-d8-41-56-c5-63-56-88-c0.com/2009/01/19/my-emacs-config-on-github/

ipython is also useful to try out functionality or debug.
