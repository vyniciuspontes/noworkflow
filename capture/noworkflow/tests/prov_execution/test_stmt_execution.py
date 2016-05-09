# Copyright (c) 2016 Universidade Federal Fluminense (UFF)
# Copyright (c) 2016 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.
"""Test Stmt collection"""
from __future__ import (absolute_import, print_function,
                        division, unicode_literals)


from ..collection_testcase import CollectionTestCase


class TestStmtExecution(CollectionTestCase):
    """Test Excution Stmt collection"""

    def test_assign_to_name(self):
        """Test assign collection"""
        self.script("# script.py\n"
                    "a = 2\n"
                    "# other")

        var_evaluation = self.get_evaluation(name="a")

        script_eval = self.get_evaluation(name="script.py")
        script_act = self.metascript.activations_store[script_eval.id]

        self.assertEqual(var_evaluation.activation_id, script_eval.id)
        self.assertTrue(bool(var_evaluation.moment))
        self.assertEqual(script_act.context['a'], var_evaluation)

        var_value = self.metascript.values_store[var_evaluation.value_id]
        var_type = self.metascript.values_store[var_value.type_id]
        type_type = self.metascript.values_store[var_type.type_id]

        self.assertEqual(var_value.value, "2")
        self.assertEqual(var_type.value, self.rtype("int"))
        self.assertEqual(type_type.value, self.rtype("type"))

    def test_assign_name_to_name(self):
        """Test assign collection"""
        self.script("# script.py\n"
                    "a = 2\n"
                    "b = a\n"
                    "# other")

        write_a_eval = self.get_evaluation(name="a", mode="w")
        read_a_eval = self.get_evaluation(name="a", mode="r")
        write_b_eval = self.get_evaluation(name="b", mode="w")

        script_eval = self.get_evaluation(name="script.py")
        script_act = self.metascript.activations_store[script_eval.id]

        self.assertEqual(read_a_eval.activation_id, script_eval.id)
        self.assertTrue(bool(read_a_eval.moment))
        self.assertEqual(write_b_eval.activation_id, script_eval.id)
        self.assertTrue(bool(write_b_eval.moment))
        self.assertEqual(script_act.context['a'], write_a_eval)
        self.assertEqual(script_act.context['b'], write_b_eval)

        self.assertEqual(read_a_eval.value_id,
                         write_a_eval.value_id)
        a_value = self.metascript.values_store[read_a_eval.value_id]
        b_value = self.metascript.values_store[write_b_eval.value_id]
        a_type = self.metascript.values_store[a_value.type_id]
        b_type = self.metascript.values_store[b_value.type_id]

        self.assertNotEqual(a_value.id, b_value.id)

        self.assertEqual(a_value.value, "2")
        self.assertEqual(b_value.value, "2")
        self.assertEqual(a_type.id, b_type.id)

        self.assertIsNotNone(self.find_dependency(
            dependent_id=read_a_eval.id, dependency_id=write_a_eval.id,
            type="assignment"
        ))
        self.assertIsNotNone(self.find_dependency(
            dependent_id=write_b_eval.id, dependency_id=read_a_eval.id,
            type="dependency"
        ))
