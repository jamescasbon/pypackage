pypackage
=========

Create RPMs or DEBs from a requirement file.

Example
-------

Create a pip requirements file:
    $ cat pyvcf.txt
    cython
    pysam
    pyvcf

Run pypackage on it: 
    $ pypackage.py pyvcf.txt
    ...
    Created deb package {"path":"/home/james/Src/scratch/pyvcf_1.0_i386.deb"}

What it does
------------

This script creates a virtual environment, uses pip to install your requirements, 
fixes up the environment to use the correct paths and then uses fpm to build 
a DEB/RPM.

Why
---

Because you want to ship an entire virtual environment and not rely on system 
packages for python or python libraries.

Installing
----------

For the moment, you need to install fpm (`gem install fpm`) and ensure it is 
on your PATH.  Then clone this repository and run `pypackage.py`.


