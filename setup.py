import setuptools

setuptools.setup(
    name='mffpy',
    version='0.5.1',
    packages=setuptools.find_packages(),
    scripts=['./bin/mff2json.py', './bin/mff2mfz.py'],
    author='Justus Schwabedal, Wayne Manselle',
    author_email='jschwabedal@belco.tech, wayne.manselle@belco.tech',
    maintainer='Evan Hathaway',
    maintainer_email='evan.hathaway@belco.tech',
    description="Reader and Writer for Philips' MFF file format.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
