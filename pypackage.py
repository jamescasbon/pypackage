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
import virtualenv


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
        logging.info('creating environment in %s...', self.venv)
        virtualenv.create_environment(self.venv, clear=True)
        logging.info('installing requirements')
        subprocess.check_call([self.pip, 'install', '--requirement', self.requirements])

    def make_relocatable(self):
        """ remove the build directory from the shebangs in the bin dir """
        logging.info('Making relocatable')
        new_shebang = '#!' + os.path.join('/', self.root, 'bin', 'python')
        virtualenv.fixup_scripts(self.venv, new_shebang, use_activate=False)
        virtualenv.fixup_pth_and_egg_link(self.venv)

        logging.info('relinking local directories')
        # FIXME: these seem to be an ubuntu hack looking at the
        # virtualenv source, should be fixed by make relocatable
        for src in glob.glob(os.path.join(self.venv, 'local', '*')):
            dst = os.path.join('/', self.root, os.path.basename(src))
            logging.debug('linking %s to %s', src, dst)
            os.remove(src)
            os.system('ln -s %(dst)s %(src)s' % locals())

    def package(self, ptype):
        """ Call FPM to build the package """
        subprocess.check_call(['fpm',
                               '-s', 'dir',
                               '-t', ptype,
                               '-C', self.build_dir,
                               '-n', self.name,
                               self.root])

def main(args):
    build_dir = 'build'#tempfile.mkdtemp()

    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    try:
        env = Environment(build_dir, args.root, args.name, args.requirements)
        env.create()
        env.make_relocatable()
        env.package(args.type)
    finally:
        pass
        # shutil.rmtree(build_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    parser.add_argument('requirements')
    parser.add_argument('--name')
    parser.add_argument('--root')
    parser.add_argument('-t', '--type', default='deb')

    logging.basicConfig(level=logging.DEBUG)

    args = parser.parse_args()
    main(args)
