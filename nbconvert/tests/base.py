"""Base test class for nbconvert"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import io
import os
import glob
import shlex
import shutil
import sys
import unittest
from subprocess import Popen, PIPE

import nose.tools as nt

from nbformat import v4, write
from ipython_genutils.tempdir import TemporaryWorkingDirectory

from ipython_genutils.py3compat import string_types, bytes_to_str

class TestsBase(unittest.TestCase):
    """Base tests class.  Contains useful fuzzy comparison and nbconvert
    functions."""


    def fuzzy_compare(self, a, b, newlines_are_spaces=True, tabs_are_spaces=True, 
                      fuzzy_spacing=True, ignore_spaces=False, 
                      ignore_newlines=False, case_sensitive=False, leave_padding=False):
        """
        Performs a fuzzy comparison of two strings.  A fuzzy comparison is a
        comparison that ignores insignificant differences in the two comparands.
        The significance of certain differences can be specified via the keyword
        parameters of this method.
        """

        if not leave_padding:
            a = a.strip()
            b = b.strip()

        if ignore_newlines:
            a = a.replace('\n', '')
            b = b.replace('\n', '')

        if newlines_are_spaces:
            a = a.replace('\n', ' ')
            b = b.replace('\n', ' ')

        if tabs_are_spaces:
            a = a.replace('\t', ' ')
            b = b.replace('\t', ' ')

        if ignore_spaces:
            a = a.replace(' ', '')
            b = b.replace(' ', '')

        if fuzzy_spacing:
            a = self.recursive_replace(a, '  ', ' ')
            b = self.recursive_replace(b, '  ', ' ')

        if not case_sensitive:
            a = a.lower()
            b = b.lower()

        self.assertEqual(a, b)


    def recursive_replace(self, text, search, replacement):
        """
        Performs a recursive replacement operation.  Replaces all instances
        of a search string in a text string with a replacement string until
        the search string no longer exists.  Recursion is needed because the
        replacement string may generate additional search strings.

        For example:
           Replace "ii" with "i" in the string "Hiiii" yields "Hii"
           Another replacement cds "Hi" (the desired output)

        Parameters
        ----------
        text : string
            Text to replace in.
        search : string
            String to search for within "text"
        replacement : string
            String to replace "search" with
        """
        while search in text:
            text = text.replace(search, replacement)
        return text

    def create_temp_cwd(self, copy_filenames=None):
        temp_dir = TemporaryWorkingDirectory()

        #Copy the files if requested.
        if copy_filenames is not None:
            self.copy_files_to(copy_filenames, dest=temp_dir.name)

        #Return directory handler
        return temp_dir
    
    def create_empty_notebook(self, path):
        nb = v4.new_notebook()
        with io.open(path, 'w', encoding='utf-8') as f:
            write(nb, f, 4)

    def copy_files_to(self, copy_filenames, dest='.'):
        "Copy test files into the destination directory"
        if not os.path.isdir(dest):
            os.makedirs(dest)
        files_path = self._get_files_path()
        for pattern in copy_filenames:
            files = glob.glob(os.path.join(files_path, pattern))
            assert files
            for match in files:
                shutil.copyfile(match, os.path.join(dest, os.path.basename(match)))


    def _get_files_path(self):

        #Get the relative path to this module in the IPython directory.
        names = self.__module__.split('.')[1:-1]
        names.append('files')
        
        #Build a path using the nbconvert directory and the relative path we just
        #found.
        import nbconvert
        path = os.path.dirname(nbconvert.__file__)
        return os.path.join(path, *names)


    def nbconvert(self, parameters, ignore_return_code=False):
        """
        Run nbconvert a, IPython shell command, listening for both Errors and non-zero
        return codes.

        Parameters
        ----------
        parameters : str, list(str)
            List of parameters to pass to IPython.
        ignore_return_code : optional bool (default False)
            Throw an OSError if the return code 
        """
        if isinstance(parameters, string_types):
            parameters = shlex.split(parameters)
        cmd = [sys.executable, '-m', 'nbconvert'] + parameters
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if not (p.returncode == 0 or ignore_return_code):
            raise OSError(bytes_to_str(stderr))
        return stdout.decode('utf8', 'replace'), stderr.decode('utf8', 'replace')


def assert_big_text_equal(a, b, chunk_size=80):
    """assert that large strings are equal

    Zooms in on first chunk that differs,
    to give better info than vanilla assertEqual for large text blobs.
    """
    for i in range(0, len(a), chunk_size):
        chunk_a = a[i:i + chunk_size]
        chunk_b = b[i:i + chunk_size]
        nt.assert_equal(chunk_a, chunk_b, "[offset: %i]\n%r != \n%r" % (
            i, chunk_a, chunk_b))

    if len(a) > len(b):
        nt.fail("Length doesn't match (%i > %i). Extra text:\n%r" % (
            len(a), len(b), a[len(b):]
        ))
    elif len(a) < len(b):
        nt.fail("Length doesn't match (%i < %i). Extra text:\n%r" % (
            len(a), len(b), b[len(a):]
        ))
