# Copyright (c) 2014 Universidade Federal Fluminense (UFF)
# Copyright (c) 2014 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.

from __future__ import (absolute_import, print_function,
                        division, unicode_literals)


import sys
import os
import traceback
import time
from profile import Profile
from datetime import datetime
from .base import ExecutionProvider
from .argument_captors import ProfilerArgumentCaptor
from ..persistence import persistence
from ..persistence.data_objects import ActivationLW, ObjectValueLW
from ..persistence.data_objects import ObjectStore, FileAccessLW
from ..cross_version import builtins
from ..models import Activation, ObjectValue, FileAccess, Trial


class Profiler(ExecutionProvider):

    def __init__(self, *args):
        super(Profiler, self).__init__(*args)
        # Open
        persistence.std_open = open
        builtins.open = self.new_open(open)

        # the number of user functions activated
        #   (starts with -1 to compensate the first call to the script itself)
        self.depth_user = -1
        # the number of non-user functions activated
        self.depth_non_user = 0
        # The first caller is None
        self.activation_stack = [None]

        # Store provenance
        self.activations = ObjectStore(ActivationLW)
        self.object_values = ObjectStore(ObjectValueLW)
        self.file_accesses = ObjectStore(FileAccessLW)

        # Avoid using the same event for tracer and profiler
        self.last_event = None

        self.definition = self.metascript.definition
        self.function_globals = self.definition.function_globals

        self.event_map['c_call'] = self.trace_c_call
        self.event_map['call'] = self.trace_call
        self.event_map['c_return'] = self.trace_c_return
        self.event_map['c_exception'] = self.trace_c_exception
        self.event_map['return'] = self.trace_return

        # Partial save
        self.save_frequency = self.metascript.save_frequency / 1000.0
        self.call_storage_frequency = self.metascript.call_storage_frequency
        self.closed_activations = 0

        self.timer = time.time
        self.last_time = self.timer()

        # Events are unique
        self.unique_events = True

        # Skip tear_up return
        self.skip_first_return = True
        self.enabled = True

        # Capture arguments
        self.argument_captor = ProfilerArgumentCaptor(self)

    @property
    def current_activation(self):
        return self._current_activation()

    @property
    def parent_activation(self):
        return self.activations[self.activation_stack[-2]]

    def _current_activation(self, ignore_open=False):
        astack = self.activation_stack
        if astack[-1] is not None:
            activation = self.activations[astack[-1]]
            if ignore_open and len(astack) > 1 and activation.name == 'open':
                # get open's parent activation
                return self.activations[astack[-2]]
            return activation
        return ActivationLW(-1, 'empty', 0, 0, -1)

    def new_open(self, old_open):
        """Wraps the open builtin function to register file access"""
        def open(name, *args, **kwargs):  # @ReservedAssignment
            if self.enabled:
                # Create a file access object with default values
                fid = self.file_accesses.add(name)
                file_access = self.file_accesses[fid]

                if os.path.exists(name):
                    # Read previous content if file exists
                    with old_open(name, 'rb') as f:
                        file_access.content_hash_before = persistence.put(
                            f.read())

                # Update with the informed keyword arguments (mode / buffering)
                file_access.update(kwargs)
                # Update with the informed positional arguments
                if len(args) > 0:
                    file_access.mode = args[0]
                elif len(args) > 1:
                    file_access.buffering = args[1]

                self.add_file_access(file_access)
            return old_open(name, *args, **kwargs)

        return open

    def add_file_access(self, file_access):
        # Wait activation that called open to finish
        activation = self._current_activation(ignore_open=True)
        file_access.function_activation_id = activation.id
        activation.file_accesses.append(file_access)

    def valid_depth(self):
        depth = self.depth_user + self.depth_non_user
        if depth < 0:
            self.enabled = False
            return False
        if depth > self.depth_threshold:
            return False
        return self.depth_non_user <= self.non_user_depth_threshold

    def add_activation(self, aid):
        self.activation_stack.append(aid)

    def close_activation(self, frame, event, arg, ccall=False):
        activation = self.current_activation
        self.activation_stack.pop()
        activation.finish = datetime.now()
        try:
            if event == 'return':
                activation.return_value = self.serialize(arg)
        except:  # ignoring any exception during capture
            activation.return_value = None
        # Update content of accessed files
        for file_access in activation.file_accesses:
            # Checks if file still exists
            if os.path.exists(file_access.name):
                with persistence.std_open(file_access.name, 'rb') as f:
                    file_access.content_hash_after = persistence.put(f.read())
            file_access.done = True
        self.closed_activations += 1
        if self.call_storage_frequency and self.closed_activations % self.call_storage_frequency == 0:
            self.store(partial=True)

    def trace_c_call(self, frame, event, arg):
        self.depth_non_user += 1
        if self.valid_depth():
            self.add_activation(self.activations.add(
                arg.__name__ if arg.__self__ == None else '.'.join(
                    [type(arg.__self__).__name__, arg.__name__]),
                frame.f_lineno, frame.f_lasti, self.activation_stack[-1]
            ))

    def trace_call(self, frame, event, arg):
        co_name = frame.f_code.co_name
        co_filename = frame.f_code.co_filename
        if co_filename in self.paths:
            self.depth_user += 1
        else:
            self.depth_non_user += 1

        if self.valid_depth():
            aid = self.activations.add(
                co_name if co_name != '<module>' else co_filename,
                frame.f_back.f_lineno, frame.f_back.f_lasti,
                self.activation_stack[-1]
            )
            activation = self.activations[aid]
            # Capturing arguments
            self.argument_captor.capture(frame, activation)

            # Capturing globals
            def_globals = self.function_globals[co_filename][activation.name]
            fglobals = frame.f_globals
            for global_var in def_globals:
                self.object_values.add(
                    global_var, self.serialize(fglobals[global_var]),
                    'GLOBAL', aid)

            activation.start = datetime.now()
            self.add_activation(aid)

    def trace_c_return(self, frame, event, arg):
        if self.valid_depth():
            self.close_activation(frame, event, arg, ccall=True)
        self.depth_non_user -= 1

    def trace_c_exception(self, frame, event, arg):
        if self.valid_depth():
            self.close_activation(frame, event, arg)
        self.depth_non_user -= 1

    def trace_return(self, frame, event, arg):
        # Only enable activations gathering after the first call to the script
        if self.skip_first_return:
            self.skip_first_return = False
            return
        if self.valid_depth():
            self.close_activation(frame, event, arg)

        if frame.f_code.co_filename in self.paths:
            self.depth_user -= 1
        else:
            self.depth_non_user -= 1

    def new_event(self, frame, event, arg):
        current_event = (event, frame.f_lineno, id(frame))
        if self.last_event != current_event:
            self.last_event = current_event
            return True
        return False

    def tracer(self, frame, event, arg):
        try:
            if self.enabled:
                if self.unique_events or self.new_event(frame, event, arg):
                    self.pre_tracer(frame, event, arg)
                    super(Profiler, self).tracer(frame, event, arg)
                if self.save_frequency and self.timer() - self.last_time > self.save_frequency:
                    self.store(partial=True)
                    self.last_time = self.timer()
        except:
            traceback.print_exc()
        finally:
            return self.tracer

    def pre_tracer(self, frame, event, arg):
        pass

    def store(self, partial=False):
        tid = self.trial_id
        if not partial:
            now = datetime.now()
            Trial.fast_update(tid, now)

        Activation.fast_store(tid, self.activations, partial)
        ObjectValue.fast_store(tid, self.object_values, partial)
        FileAccess.fast_store(tid, self.file_accesses, partial)

    def tearup(self):
        sys.setprofile(self.tracer)

    def teardown(self):
        builtins.open = persistence.std_open
        super(Profiler, self).teardown()
        sys.setprofile(self.default_profile)
