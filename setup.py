from os.path import join
import setuptools

# We expect "mffpy/version.py" to be very simple:
#
# > __version__ = "x.y.z"
#
# (from one of the answers in
# https://stackoverflow.com/questions/458550/standard-way-to-embed-version-into-python-package)
__version__ = ''
exec(open(join('mffpy', 'version.py')).read())
requirements = open('requirements.txt').read().split('\n')

setuptools.setup(
    name='mffpy',
    version=__version__,
    packages=setuptools.find_packages(),
    scripts=['./bin/mff2json.py', './bin/mff2mfz.py', './bin/mffdiff.py'],
    author='Justus Schwabedal, Wayne Manselle',
    author_email='jschwabedal@belco.tech, wayne.manselle@belco.tech',
    maintainer='Evan Hathaway',
    maintainer_email='evan.hathaway@belco.tech',
    description="Reader and Writer for Philips' MFF file format.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
