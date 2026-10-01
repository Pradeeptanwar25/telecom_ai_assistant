# ============================================================
# test_integration_ai.py
#
# Integration Tracker AI automated test suite
#
# Flow:
#
# Natural Language
#       ↓
# Query Parser
#       ↓
# Validator
#       ↓
# PostgreSQL
#       ↓
# Exact Result
#
# IMPORTANT:
# No question-specific answer is hard-coded.
# ============================================================

import os
import sys
import json
import unittest
from pprint import pprint


# ============================================================
# DJANGO SETUP
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)


import django

django.setup()


# ============================================================
# PROJECT IMPORTS
# ============================================================

from integration.query_parser import (
    parse_user_query,
)

from integration.query_validator import (
    validate_query_plan,
    QueryValidationError,
)

from integration.query_engine import (
    execute_integration_query,
)

from integration.answer_generator import (
    generate_answer,
)


# ============================================================
# HELPER
# ============================================================

def run_question(question):
    """
    Complete AI pipeline for one question.
    """

    print()
    print("=" * 80)
    print("QUESTION:")
    print(question)
    print("=" * 80)

    # --------------------------------------------------------
    # Parser
    # --------------------------------------------------------

    query_plan = parse_user_query(
        question
    )

    print("\nQUERY PLAN:")
    pprint(query_plan)

    # --------------------------------------------------------
    # Explicit validation
    # --------------------------------------------------------

    validated_plan = validate_query_plan(
        query_plan
    )

    # --------------------------------------------------------
    # PostgreSQL
    # --------------------------------------------------------

    result = execute_integration_query(
        filters=validated_plan.get(
            "filters",
            [],
        ),
        operation=validated_plan.get(
            "operation",
            "retrieve",
        ),
        limit=validated_plan.get(
            "limit",
            500,
        ),
        fields=validated_plan.get(
            "fields",
            [],
        ),
        group_by=validated_plan.get(
            "group_by",
            [],
        ),
        aggregation=validated_plan.get(
            "aggregation",
            None,
        ),
        sort=validated_plan.get(
            "sort",
            [],
        ),
        aggregation_field=validated_plan.get(
            "aggregation_field",
            None,
        ),
    )

    print("\nDATABASE RESULT:")

    pprint(result)

    # --------------------------------------------------------
    # Final answer
    # --------------------------------------------------------

    answer = generate_answer(
        question,
        validated_plan,
        result,
    )

    print("\nFINAL ANSWER:")
    print(answer)

    return (
        validated_plan,
        result,
        answer,
    )


# ============================================================
# TEST CLASS
# ============================================================

class IntegrationAIUnitTests(
    unittest.TestCase
):

    # ========================================================
    # TEST 1
    # Basic count question
    # ========================================================

    def test_basic_count(self):

        question = (
            "Integration Tracker mein "
            "total kitne records hain?"
        )

        query_plan = parse_user_query(
            question
        )

        self.assertEqual(
            query_plan["operation"],
            "count",
        )

        result = execute_integration_query(
            filters=query_plan["filters"],
            operation=query_plan["operation"],
            limit=query_plan["limit"],
            fields=query_plan["fields"],
            group_by=query_plan["group_by"],
            aggregation=query_plan["aggregation"],
            sort=query_plan["sort"],
            aggregation_field=query_plan[
                "aggregation_field"
            ],
        )

        self.assertIn(
            "count",
            result,
        )

        self.assertIsInstance(
            result["count"],
            int,
        )

        self.assertEqual(
            result["records"],
            [],
        )


    # ========================================================
    # TEST 2
    # Dynamic categorical filter
    # ========================================================

    def test_dynamic_activity_filter(self):

        question = (
            "RET ka total count batao"
        )

        query_plan = parse_user_query(
            question
        )

        self.assertEqual(
            query_plan["operation"],
            "count",
        )

        self.assertTrue(
            len(
                query_plan["filters"]
            ) > 0
        )

        # Find whether parser selected a field
        # related to the question.
        activity_filters = [
            item
            for item in query_plan["filters"]
            if item.get("field")
            == "activity_name"
        ]

        self.assertTrue(
            activity_filters,
            "Parser did not identify activity_name."
        )

        result = execute_integration_query(
            filters=query_plan["filters"],
            operation=query_plan["operation"],
            limit=query_plan["limit"],
            fields=query_plan["fields"],
            group_by=query_plan["group_by"],
            aggregation=query_plan["aggregation"],
            sort=query_plan["sort"],
            aggregation_field=query_plan[
                "aggregation_field"
            ],
        )

        self.assertIn(
            "count",
            result,
        )

        self.assertIsInstance(
            result["count"],
            int,
        )


    # ========================================================
    # TEST 3
    # Circle filter
    # ========================================================

    def test_circle_count(self):

        question = (
            "AP mein kitne records hain?"
        )

        query_plan = parse_user_query(
            question
        )

        self.assertEqual(
            query_plan["operation"],
            "count",
        )

        circle_filters = [
            item
            for item in query_plan["filters"]
            if item.get("field")
            == "circle"
        ]

        self.assertTrue(
            circle_filters,
            "Parser did not identify circle."
        )

        result = execute_integration_query(
            filters=query_plan["filters"],
            operation=query_plan["operation"],
            limit=query_plan["limit"],
            fields=query_plan["fields"],
            group_by=query_plan["group_by"],
            aggregation=query_plan["aggregation"],
            sort=query_plan["sort"],
            aggregation_field=query_plan[
                "aggregation_field"
            ],
        )

        self.assertIsInstance(
            result["count"],
            int,
        )


    # ========================================================
    # TEST 4
    # Grouped aggregation
    # ========================================================

    def test_circle_wise_count(self):

        question = (
            "circle wise integration count batao"
        )

        query_plan = parse_user_query(
            question
        )

        self.assertEqual(
            query_plan["operation"],
            "aggregate",
        )

        self.assertEqual(
            query_plan["aggregation"],
            "count",
        )

        self.assertTrue(
            query_plan["group_by"],
            "group_by should not be empty."
        )

        result = execute_integration_query(
            filters=query_plan["filters"],
            operation=query_plan["operation"],
            limit=query_plan["limit"],
            fields=query_plan["fields"],
            group_by=query_plan["group_by"],
            aggregation=query_plan["aggregation"],
            sort=query_plan["sort"],
            aggregation_field=query_plan[
                "aggregation_field"
            ],
        )

        self.assertTrue(
            isinstance(
                result["records"],
                list,
            )
        )


    # ========================================================
    # TEST 5
    # Multiple group fields
    # ========================================================

    def test_circle_activity_count(self):

        question = (
            "circle aur activity wise count batao"
        )

        query_plan = parse_user_query(
            question
        )

        self.assertEqual(
            query_plan["operation"],
            "aggregate",
        )

        self.assertEqual(
            query_plan["aggregation"],
            "count",
        )

        self.assertGreaterEqual(
            len(
                query_plan["group_by"]
            ),
            1,
        )

        result = execute_integration_query(
            filters=query_plan["filters"],
            operation=query_plan["operation"],
            limit=query_plan["limit"],
            fields=query_plan["fields"],
            group_by=query_plan["group_by"],
            aggregation=query_plan["aggregation"],
            sort=query_plan["sort"],
            aggregation_field=query_plan[
                "aggregation_field"
            ],
        )

        self.assertIsInstance(
            result["records"],
            list,
        )


    # ========================================================
    # TEST 6
    # Exact date query
    # ========================================================

    def test_exact_date_query(self):

        question = (
            "AP ke 12 September 2025 ke "
            "activity names batao"
        )

        query_plan = parse_user_query(
            question
        )

        self.assertEqual(
            query_plan["operation"],
            "retrieve",
        )

        self.assertTrue(
            query_plan["filters"],
        )

        date_filters = [
            item
            for item in query_plan["filters"]
            if item.get("field")
            == "integration_date"
        ]

        self.assertTrue(
            date_filters,
            "Parser did not identify integration_date."
        )

        self.assertIn(
            "activity_name",
            query_plan["fields"],
        )

        result = execute_integration_query(
            filters=query_plan["filters"],
            operation=query_plan["operation"],
            limit=query_plan["limit"],
            fields=query_plan["fields"],
            group_by=query_plan["group_by"],
            aggregation=query_plan["aggregation"],
            sort=query_plan["sort"],
            aggregation_field=query_plan[
                "aggregation_field"
            ],
        )

        self.assertIn(
            "count",
            result,
        )

        self.assertIsInstance(
            result["records"],
            list,
        )


    # ========================================================
    # TEST 7
    # LNBTS lookup
    # ========================================================

    def test_lnbts_lookup(self):

        question = (
            "LNBTS 911968 ki complete details do"
        )

        query_plan = parse_user_query(
            question
        )

        self.assertEqual(
            query_plan["operation"],
            "retrieve",
        )

        lnbts_filters = [
            item
            for item in query_plan["filters"]
            if item.get("field")
            == "lnbts_id"
        ]

        self.assertTrue(
            lnbts_filters,
            "Parser did not identify lnbts_id."
        )

        # Complete details should normally mean
        # fields=[].
        self.assertEqual(
            query_plan["fields"],
            [],
        )

        result = execute_integration_query(
            filters=query_plan["filters"],
            operation=query_plan["operation"],
            limit=query_plan["limit"],
            fields=query_plan["fields"],
            group_by=query_plan["group_by"],
            aggregation=query_plan["aggregation"],
            sort=query_plan["sort"],
            aggregation_field=query_plan[
                "aggregation_field"
            ],
        )

        self.assertIsInstance(
            result["records"],
            list,
        )


    # ========================================================
    # TEST 8
    # Unique key lookup
    # ========================================================

    def test_unique_key_lookup(self):

        question = (
            "unique key ki complete details dikhao "
            "2025-09-12 00:00:00DE-GROWRAH1968TDDMAH102,"
            "112911968NOKIA"
        )

        query_plan = parse_user_query(
            question
        )

        self.assertEqual(
            query_plan["operation"],
            "retrieve",
        )

        unique_key_filters = [
            item
            for item in query_plan["filters"]
            if item.get("field")
            == "unique_key"
        ]

        self.assertTrue(
            unique_key_filters,
            "Parser did not identify unique_key."
        )

        unique_key_value = (
            unique_key_filters[0]
            .get("value")
        )

        self.assertTrue(
            unique_key_value
        )

        # The complete value must remain intact.
        self.assertIn(
            "DE-GROW",
            unique_key_value,
        )

        self.assertIn(
            "NOKIA",
            unique_key_value,
        )

        result = execute_integration_query(
            filters=query_plan["filters"],
            operation=query_plan["operation"],
            limit=query_plan["limit"],
            fields=query_plan["fields"],
            group_by=query_plan["group_by"],
            aggregation=query_plan["aggregation"],
            sort=query_plan["sort"],
            aggregation_field=query_plan[
                "aggregation_field"
            ],
        )

        self.assertIsInstance(
            result["records"],
            list,
        )


    # ========================================================
    # TEST 9
    # Numeric aggregation
    # ========================================================

    def test_numeric_aggregation(self):

        question = (
            "total cell count batao"
        )

        query_plan = parse_user_query(
            question
        )

        self.assertEqual(
            query_plan["operation"],
            "aggregate",
        )

        self.assertEqual(
            query_plan["aggregation"],
            "sum",
        )

        self.assertTrue(
            query_plan["aggregation_field"]
        )

        result = execute_integration_query(
            filters=query_plan["filters"],
            operation=query_plan["operation"],
            limit=query_plan["limit"],
            fields=query_plan["fields"],
            group_by=query_plan["group_by"],
            aggregation=query_plan["aggregation"],
            sort=query_plan["sort"],
            aggregation_field=query_plan[
                "aggregation_field"
            ],
        )

        self.assertIsInstance(
            result["records"],
            list,
        )


    # ========================================================
    # TEST 10
    # Empty result should not crash
    # ========================================================

    def test_empty_result(self):

        question = (
            "records where unique_key equals "
            "THIS_VALUE_SHOULD_NOT_EXIST_123456789"
        )

        query_plan = parse_user_query(
            question
        )

        result = execute_integration_query(
            filters=query_plan["filters"],
            operation=query_plan["operation"],
            limit=query_plan["limit"],
            fields=query_plan["fields"],
            group_by=query_plan["group_by"],
            aggregation=query_plan["aggregation"],
            sort=query_plan["sort"],
            aggregation_field=query_plan[
                "aggregation_field"
            ],
        )

        self.assertEqual(
            result["count"],
            0,
        )

        self.assertEqual(
            result["records"],
            [],
        )


    # ========================================================
    # TEST 11
    # Final answer generation
    # ========================================================

    def test_final_answer_generation(self):

        question = (
            "RET ka total count batao"
        )

        query_plan = parse_user_query(
            question
        )

        result = execute_integration_query(
            filters=query_plan["filters"],
            operation=query_plan["operation"],
            limit=query_plan["limit"],
            fields=query_plan["fields"],
            group_by=query_plan["group_by"],
            aggregation=query_plan["aggregation"],
            sort=query_plan["sort"],
            aggregation_field=query_plan[
                "aggregation_field"
            ],
        )

        answer = generate_answer(
            question,
            query_plan,
            result,
        )

        self.assertIsInstance(
            answer,
            str,
        )

        self.assertTrue(
            answer.strip()
        )

        # The exact DB count must appear in the
        # deterministic count answer.
        count_text = str(
            result["count"]
        )

        self.assertIn(
            count_text,
            answer,
        )


# ============================================================
# DATA INSPECTION MODE
# ============================================================

def run_data_inspection():
    """
    Run a set of natural-language questions and print
    the dynamically generated plans and actual DB results.

    This is NOT a pass/fail test.
    It is useful when you want to inspect what the AI
    understands.
    """

    questions = [

        "Integration Tracker mein total kitne records hain?",

        "RET ka total count batao",

        "AP me kitne records hain?",

        "circle wise integration count batao",

        "circle aur activity wise count batao",

        "AP ke 12 September 2025 ke activity names batao",

        "LNBTS 911968 ki complete details do",

        "Nokia ke MAH records dikhao",

        "total cell count batao",

    ]

    print()
    print("#" * 80)
    print("INTEGRATION AI DATA INSPECTION")
    print("#" * 80)

    for question in questions:

        try:

            plan, result, answer = (
                run_question(
                    question
                )
            )

            print("\n" + "-" * 80)
            print("SUMMARY")
            print("-" * 80)

            print(
                "Operation:",
                plan.get(
                    "operation"
                ),
            )

            print(
                "Count:",
                result.get(
                    "count"
                ),
            )

            print(
                "Records returned:",
                len(
                    result.get(
                        "records",
                        [],
                    )
                ),
            )

            print(
                "Answer:",
                answer,
            )

        except Exception as exc:

            print()
            print(
                "ERROR:",
                exc,
            )

            print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Normal:
    #
    # python test_integration_ai.py
    #
    # --------------------------------------------------------

    if "--data-check" not in sys.argv:

        unittest.main(
            verbosity=2
        )

    # --------------------------------------------------------
    # Inspection:
    #
    # python test_integration_ai.py --data-check
    #
    # --------------------------------------------------------

    else:

        run_data_inspection()