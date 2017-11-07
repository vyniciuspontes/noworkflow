# Copyright (c) 2016 Universidade Federal Fluminense (UFF)
# Copyright (c) 2016 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.
"""Content Database Factory"""
from __future__ import (absolute_import, print_function,
                        division, unicode_literals)
from .content_database_standart import ContentDatabaseStandart

from .content_database_pure_git import ContentDatabasePureGit


CONTENT_DIRNAME = "content"


class ContentDatabaseFactory(object):
    """Content Database deal with storage of file content in disk"""

    @staticmethod
    def factory(persistence_config):
        return ContentDatabasePureGit(persistence_config)
