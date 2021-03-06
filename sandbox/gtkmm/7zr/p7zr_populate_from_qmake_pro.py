#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import os
import shutil
import argparse
import re

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.join(SCRIPT_DIR, "src")
MAKEFILE_AM_TEMPLATE = os.path.join(SCRIPT_DIR, "template_Makefile.am")
MAKEFILE_AM_TARGET = os.path.join(SCRIPT_DIR, "Makefile.am")
CONFIGURE_AC_TEMPLATE = os.path.join(SCRIPT_DIR, "template_configure.ac")
CONFIGURE_AC_TARGET = os.path.join(SCRIPT_DIR, "configure.ac")


class P7ZRAutotools(object):


    def __init__(self, p7zip_sources, dry_run):
        self._p7zip_sources = p7zip_sources
        self._dry_run = dry_run

        self._version = os.path.basename(self._p7zip_sources).split("_")[-1]
        print self._version
        self._all_includedirs_from = []
        self._all_sourcefiles_to = []
        self._all_headerfiles_to = []


    def _get_pro_paths(self, qmake_pro_dirpath, qmake_pro_filepath, starting_token):

        with open(qmake_pro_filepath, "r") as fd:
            target_acquired = False
            for str_line in fd:
                str_line_clean = str_line.replace("\n", "").replace("\r", "")
                if target_acquired is False:
                    if str_line_clean.startswith(starting_token):
                        target_acquired = True
                else:
                    if not str_line_clean.endswith(" \\"):
                        break
                    path = os.path.realpath(os.path.join(qmake_pro_dirpath, str_line[:-2].strip()))
                    assert os.path.exists(path)
                    yield path


    def _source_parse_headers(self, filepath):

        with open(filepath, "r") as fd:
            txt_content = fd.read()
        matches = re.findall(r'#include\s+\"([^\"]+)\"', txt_content, re.MULTILINE)
        for head_rel_path in matches:
            #print headpath
            this_dirpath = os.path.dirname(filepath)
            for curr_dirpath in ([this_dirpath] + self._all_includedirs_from):
                headpath = os.path.realpath(os.path.join(curr_dirpath, head_rel_path))
                if os.path.isfile(headpath):
                    self._filepath_to_copy(headpath)
                    break


    def _filepath_do_copy(self, filepath, target_filepath):

        if self._dry_run is True:
            print "{} -> {}".format(filepath, target_filepath)
        else:
            target_dirpath = os.path.dirname(target_filepath)
            if not os.path.isdir(target_dirpath):
                os.makedirs(target_dirpath)
            shutil.copyfile(filepath, target_filepath)


    def _filepath_to_copy(self, filepath):

        rel_filepath = os.path.relpath(filepath, self._p7zip_sources)
        target_filepath = os.path.join(SRC_DIR, rel_filepath)

        if self._is_header(filepath):
            if target_filepath not in self._all_headerfiles_to:
                self._all_headerfiles_to.append(target_filepath)
                self._filepath_do_copy(filepath, target_filepath)
        else:
            if target_filepath not in self._all_sourcefiles_to:
                self._all_sourcefiles_to.append(target_filepath)
                self._filepath_do_copy(filepath, target_filepath)
                self._source_parse_headers(filepath)


    def _is_header(self, filepath):

        return filepath.rsplit(".", 2)[-1] in ("h", "H")


    def generate(self):

        qmake_pro_dirpath = os.path.join(self._p7zip_sources, "CPP", "7zip", "QMAKE", "7zr")
        qmake_pro_filepath = os.path.join(qmake_pro_dirpath, "7zr.pro")

        for dirpath in self._get_pro_paths(qmake_pro_dirpath, qmake_pro_filepath, "INCLUDEPATH ="):
            self._all_includedirs_from.append(dirpath)
            #print dirpath

        for filepath in self._get_pro_paths(qmake_pro_dirpath, qmake_pro_filepath, "SOURCES +="):
            self._filepath_to_copy(filepath)


if "__main__" == __name__:
    parser = argparse.ArgumentParser()
    parser.add_argument('p7zip_sources', nargs='?', default="/home/giuspen/Software/p7zip_16.02", help='p7zip sources dirpath')
    parser.add_argument("-d", "--dry_run", action="store_true", help="just print, do not take any action")
    args = parser.parse_args()
    p7zr_autotools = P7ZRAutotools(args.p7zip_sources, args.dry_run)
    p7zr_autotools.generate()
