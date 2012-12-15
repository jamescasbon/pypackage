#!/usr/bin/env python
"""
Create a python distribution using FPM.
"""
import os
import sys
import argparse
import tempfile
import shutil
import logging
import subprocess
import glob


class Environment(object):

    def __init__(self, build_dir, root, name, requirements):
        self.build_dir = build_dir
        self.root = root
        self.name = name
        self.requirements = requirements

        if self.name is None:
            self.name = os.path.splitext(self.requirements)[0]

        if self.root is None:
            self.root = os.path.join('home', self.name)

        self.venv = os.path.join(self.build_dir, self.root)
        self.pip = os.path.join(self.venv, 'bin', 'pip')

    def create(self):
        """ create the environment and install packages """
        os.makedirs(self.venv)
        logging.info('creating environment in %s...', self.venv)
        subprocess.check_call(['virtualenv', self.venv])
        logging.info('installing requirements')
        subprocess.check_call([self.pip, 'install', '--requirement', self.requirements])
        logging.info('make relocatable')
        #subprocess.check_call(['virtualenv', '--relocatable', self.venv])

    def make_relocatable(self):
        """ remove the build directory from the shebangs in the bin dir """
        logging.info('changing shebangs in bin dir')
        bin_glob = os.path.join(self.venv, 'bin', '*')
        build_abs = os.path.abspath(self.build_dir)
        for fname in glob.glob(bin_glob):
            logging.debug('checking %s', fname)
            with open(fname) as filein:
                filein = iter(filein)
                try:
                    shebang = filein.next()
                except StopIteration:
                    continue
                if shebang.startswith('#!') and build_abs in shebang:
                    new_fname = fname + '.tmp'
                    shutil.copy(fname, new_fname) # preserve the permissions
                    with open(new_fname, 'w') as fileout:
                        fileout.write(shebang.replace(build_abs, ''))
                        map(fileout.write, filein)
                    shutil.move(new_fname, fname)

        logging.info('relinking local directories')
        for src in glob.glob(os.path.join(self.venv, 'local', '*')):
            dst = os.path.join('/', self.root, os.path.basename(src))
            logging.debug('linking %s to %s', src, dst)
            os.remove(src)
            os.system('ln -s %(dst)s %(src)s' % locals())


    def package(self):
        subprocess.check_call(['fpm',
                               '-s', 'dir',
                               '-t', 'deb',
                               '-C', self.build_dir,
                               '-n', self.name,
                               self.root])

def main(args):
    build_dir = 'build'#tempfile.mkdtemp()
    # os.makedirs(build_dir)
    try:
        env = Environment(build_dir, args.root, args.name, args.requirements)
        env.create()
        env.make_relocatable()
        env.package()
    finally:
        pass
        # shutil.rmtree(build_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    parser.add_argument('requirements')
    parser.add_argument('--name')
    parser.add_argument('--root')

    logging.basicConfig(level=logging.DEBUG)

    args = parser.parse_args()
    main(args)
