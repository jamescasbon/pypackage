#!/usr/bin/env python
"""
Package a pip requirements file into a deb or rpm.

This script builds a virtual environment from a requirements file,
and then creates a a package containing the environment.  The package
will contain the python interpreter and all the libraries, so is
a self contained, complete environment that does not need any
particular system python or python libraries.
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
            self.name = os.path.splitext(os.path.basename(self.requirements))[0]

        if self.root is None:
            self.root = os.path.join('home', self.name)

        self.pip = os.path.join(self.root, 'bin', 'pip')

        os.makedirs(self.build_dir)
        cwd = os.getcwd()
        os.chdir(self.build_dir)
        try:
            self._create()
            self._make_relocatable()
            self._make_path_hooks()
        finally:
            os.chdir(cwd)

    def _create(self):
        """ create the environment and install packages """
        logging.info('creating environment in %s...', self.root)
        virtualenv.create_environment(self.root, clear=True)
        logging.info('installing requirements')
        pre_install = self._pre_install_list()
        if pre_install:
            subprocess.check_call([self.pip, 'install'] + pre_install)
        subprocess.check_call([self.pip, 'install', '--requirement', self.requirements])

    def _pre_install_list(self):
        """ https://github.com/pypa/pip/issues/25 """
        return [req
                for req in file(self.requirements)
                for name in ['numpy', 'cython']
                if name in req.lower()]

    def _make_relocatable(self):
        """ remove the build directory from the shebangs in the bin dir """
        logging.info('Making relocatable')
        new_shebang = '#!' + os.path.join('/', self.root, 'bin', 'python')
        virtualenv.fixup_scripts(self.root, new_shebang, use_activate=False)
        virtualenv.fixup_pth_and_egg_link(self.root)

        logging.info('relinking local directories')
        # FIXME: these seem to be an ubuntu hack looking at the
        # virtualenv source, should be fixed by make relocatable
        for src in glob.glob(os.path.join(self.root, 'local', '*')):
            dst = os.path.join('/', self.root, os.path.basename(src))
            logging.debug('linking %s to %s', src, dst)
            os.remove(src)
            os.system('ln -s %(dst)s %(src)s' % locals())

    def _make_path_hooks(self, dirname='usr/local/bin'):
        """ create links to the binaries in the environment """
        os.makedirs(dirname)
        for fpath in glob.glob(os.path.join(self.root, 'bin', '*')):
            name = os.path.basename(fpath)
            if any([name.startswith(x)
                    for x in ['pip', 'easy_install', 'python', 'activate']]):
                continue
            src = os.path.join(dirname, name)
            dst = os.path.join('/', fpath)
            os.system('ln -s %(dst)s %(src)s' % locals())

    def package(self, ptype, args=''):
        """ Call FPM to build the package """
        cmd = ['fpm',
                '-s', 'dir',
                '-t', ptype,
                '-C', self.build_dir,
                '-n', self.name]
        if args:
            cmd += args.split()
        cmd.append('.')
        subprocess.check_call(cmd)

def main(args):
    build_dir = 'build'#tempfile.mkdtemp()
    requirements = os.path.abspath(args.requirements)
    if os.path.exists(build_dir):
        if args.delete:
            shutil.rmtree(build_dir)
        else:
            print 'build directory exists, remove it or use -d'
            sys.exit(1)
    try:
        env = Environment(build_dir, args.root, args.name, requirements)
        env.package(args.type, args.fpm_args)
    finally:
        if not args.no_cleanup:
            shutil.rmtree(build_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    parser.add_argument('requirements',
                        help='pip requirements file to use')
    parser.add_argument('--name',
                        help='name of package (defaults to the basename'
                        'of the requirements file)')
    parser.add_argument('--root',
                        help='package root (default /home/$name)')
    parser.add_argument('-t', '--type', default='deb',
                        help='package type (default deb)')
    parser.add_argument('-n', '--no-cleanup', action='store_true',
                        help='do not remove build directory')
    parser.add_argument('-d', '--delete', action='store_true',
                        help='remove build directory before starting')
    parser.add_argument('-f', '--fpm-args',
                        help='extra args for fpm')
    parser.add_argument('-c', '--cython', action='store_true',
                        help='preinstall cython')

    logging.basicConfig(level=logging.DEBUG)

    args = parser.parse_args()
    main(args)
