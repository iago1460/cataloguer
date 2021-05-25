import os

from setuptools import setup, find_packages


try:
    # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError:
    # for pip <= 9.0.3
    from pip.req import parse_requirements

import catalogue

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


def load_requirements(filename):
    reqs = list(parse_requirements(filename, session="setup"))
    try:
        return [str(ir.req) for ir in reqs]
    except AttributeError:
        return [str(ir.requirement) for ir in reqs]


setup(
    author='Iago Veloso',
    name='catalogue',
    version=catalogue.__version__,
    description='Organize your media files',
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
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    install_requires=load_requirements('requirements.txt'),
    python_requires='>=3.9',
)
