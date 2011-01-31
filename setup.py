from distutils.core import setup

setup(
    name='Pymdht',
    version='1.0',
    author='Raul Jimenez',
    author_email='rauljim@gmail.com',
    packages=['pymdht', 'pymdht.core'],
    scripts=['bin/interactive_dht.py', 'pymdht-daemon.py'],
    url='http://pypi.python.org/pypi/Pymdht/',
    license='LICENSE.txt',
    description='A flexible implementation of the Mainline DHT protocol.',
    long_description=open('README.txt').read(),
)
