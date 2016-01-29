# Copyright (c) 2016 Universidade Federal Fluminense (UFF)
# Copyright (c) 2016 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.
"""Collect definition provenance"""
from __future__ import (absolute_import, print_function,
                        division, unicode_literals)

from ..utils import print_msg, meta_profiler


@meta_profiler("definition")
def collect_provenance(metascript):
    metascript.definition.collect_provenance(metascript)
