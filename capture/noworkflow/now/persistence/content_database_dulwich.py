# Copyright (c) 2016 Universidade Federal Fluminense (UFF)
# Copyright (c) 2016 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.
"""Content Database Pure Git"""
from __future__ import (absolute_import, print_function,
                        division, unicode_literals)

from .content_database import ContentDatabase
import dulwich
import dulwich.objects as objects
from dulwich.repo import Repo
import os
from os.path import join, isdir, isfile
from os import mkdir

class ContentDatbaseDulwich(ContentDatabase):
    """Content database that uses git library Dulwich"""

    def __init(self):
        super(ContentDatabase, self).__init__()

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
            os.makedirs(self.content_path)
            Repo.init(self.content_path)

    def put(self, content):
        """Put content in the content database

        Return: content hash code

        Arguments:
        content -- binary text to be saved
        """
        repo = Repo(self.content_path)
        object_store = repo.object_store
        blob = objects.Blob.from_string(content)
        object_store.add_object(blob)

        return blob.id.decode("ascii")

    def find_subhash(self, content_hash):
        return None

    def get(self, content_hash):
        """Get content from the content database

        Return: content

        Arguments:
        content_hash -- content hash code
        """
        repo = Repo(self.content_path)
        return repo.__getitem__(content_hash)