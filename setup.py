import os

from setuptools import setup, find_packages

import catalogue

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    author='Iago Veloso',
    name='catalogue',
    version=catalogue.__version__,
    description='This app provides an easy way to set up your radio',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    url='https://github.com/iago1460/photo-cataloguer',
    packages=find_packages(),
    entry_points={
        "console_scripts": ["catalogue=catalogue.main:main"]
    },
    include_package_data=True,
    zip_safe=False,
    license='MIT',
    platforms=['OS Independent'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    install_requires=[
        'Pillow',
        'python-dateutil'
    ],
    python_requires='>=3.6',
)
