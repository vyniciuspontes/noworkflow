
# Copyright (c) 2016 Universidade Federal Fluminense (UFF)
# Copyright (c) 2016 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.
"""Content Database"""
from __future__ import (absolute_import, print_function,
                        division, unicode_literals)

import hashlib
import os

from . import git_system
from os.path import join, isdir, isfile
from .content_database import ContentDatabase

CONTENT_DIRNAME = "content"


class ContentDatabasePureGit(ContentDatabase):

    def mock(self, config):                                                      # pylint: disable=unused-argument, no-self-use
        '''"""Mock storage for tests"""
        self.temp = {}

        def put(self, content):
            """Mock put"""
            hash_code = hashlib.sha1(content).hexdigest()
            self.temp[hash_code] = content
            return hash_code

        def get(self, content_hash):
            """Mock get"""
            return self.temp[content_hash]
        ContentDatabaseStandart.put = put
        ContentDatabaseStandart.get = get'''

    def connect(self, config):
        """Create content directory"""
        if not config.should_mock and not isdir(self.content_path):
            git_system.init(self.content_path)

    def put(self, content):
        """Put content in the content database

        Return: content hash code

        Arguments:
        content -- binary text to be saved
        """
        content_hash = git_system.put(content, self.content_path)
        return content_hash

    def find_subhash(self, content_hash):
        return None

    def get(self, content_hash):
        """Get content from the content database

        Return: content

        Arguments:
        content_hash -- content hash code
        """

        return git_system.get(content_hash, self.content_path)
