from setuptools import setup

setup(
    name='mffpy',
    version='0.3.0',
    packages=['mffpy'],
    scripts=['./bin/mff2mfz.py'],
    author='Justus Schwabedal, Wayne Manselle',
    author_email='jschwabedal@belco.tech, wayne.manselle@belco.tech',
    maintainer='Justus Schwabedal',
    maintainer_email='jschwabedal@belco.tech',
    long_description=open('README.md').read(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Apache License :: Version 2.0",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
