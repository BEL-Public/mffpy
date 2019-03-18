from distutils.core import setup

setup(
    name='mffpy',
    version='0.1.0',
    packages=['mffpy'],
    scripts=['./bin/mff2mfz.py'],
    long_description=open('README.md').read(),
)
