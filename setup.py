from distutils.core import setup

setup(
    name='Pymdht',
    version='11.8.1',
    author='Raul Jimenez and others',
    author_email='rauljc@gkth.se',
    packages=['pymdht', 'pymdht.core', 'pymdht.plugins',],
    scripts=['interactive_dht.py', 'pymdht_daemon.py'],
    url='http://pypi.python.org/pypi/Pymdht/',
    license='LICENSE.txt',
    description='A flexible implementation of the Mainline DHT protocol.',
    long_description=open('README.txt').read(),
)
