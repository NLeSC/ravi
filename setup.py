from setuptools import setup

setup(
    name='Ravi',
    version='0.1',
    license='Apache 2.0',
    author='Lars Ridder',
    author_email='lars.ridder@esciencecenter.nl>',
    url='https://bitbucket.org/ridderlars/ravi',
    description='Resources Assignment and VIsualization',
    classifiers=["Natural Language :: English",
                 "Operating System :: OS Independent",
                 "Programming Language :: Python :: 2.7",
                 ],
    packages=['ravi'],
    install_requires=['flask', 'sqlalchemy'],
    entry_points={'console_scripts': ['ravi = ravi:main']}
)
