from unittest.mock import patch

from django.test import SimpleTestCase
import pandas as pd

from integration.management.commands.import_integration import _strip_string_values
from integration.query_parser import (
	_apply_generic_count_recovery,
	DATA_FIELDS,
	FIELD_ALIASES,
	FIELD_DESCRIPTIONS,
	_normalize_text_filter_case,
	parse_user_query,
	_resolve_database_values,
)


class ResolveDatabaseValuesTests(SimpleTestCase):
	def test_import_trims_whitespace_from_string_values(self):
		dataframe = pd.DataFrame({"Activity Name": ["RET ", " RET"], "Count": [" 2 ", "3"]})

		result = _strip_string_values(dataframe)

		self.assertEqual(result["Activity Name"].tolist(), ["RET", "RET"])
		self.assertEqual(result["Count"].tolist(), ["2", "3"])

	@patch("integration.query_parser._get_value_catalog")
	def test_each_database_field_can_be_resolved_from_its_label(self, get_catalog):
		for field_name in DATA_FIELDS:
			aliases = FIELD_ALIASES.get(field_name)
			label = (
				aliases[0]
				if aliases
				else FIELD_DESCRIPTIONS.get(field_name, field_name.replace("_", " "))
			)
			get_catalog.return_value = {field_name: ["VALUE123"]}
			query_plan = {"operation": "retrieve", "filters": []}

			result = _resolve_database_values(f"{label} VALUE123", query_plan)

			with self.subTest(field=field_name):
				self.assertEqual(
					result["filters"],
					[{"field": field_name, "operator": "iexact", "value": "VALUE123"}],
				)

	def test_ungrouped_count_question_becomes_count_operation(self):
		query_plan = {
			"operation": "aggregate",
			"aggregation": "count",
			"aggregation_field": "activity_name",
			"group_by": [],
		}

		result = _apply_generic_count_recovery(query_plan, "RET ka total count batao")

		self.assertEqual(result["operation"], "count")
		self.assertIsNone(result["aggregation"])
		self.assertIsNone(result["aggregation_field"])

	def test_grouped_count_remains_aggregate(self):
		query_plan = {
			"operation": "aggregate",
			"aggregation": "count",
			"group_by": ["circle"],
		}

		result = _apply_generic_count_recovery(query_plan, "circle wise count batao")

		self.assertEqual(result["operation"], "aggregate")
		self.assertEqual(result["group_by"], ["circle"])

	def test_text_exact_filter_is_case_insensitive_by_default(self):
		query_plan = {
			"filters": [
				{"field": "oem", "operator": "exact", "value": "Nokia"},
				{"field": "activity_name", "operator": "exact", "value": "RET"},
			]
		}

		result = _normalize_text_filter_case(query_plan, "nokia ret ka count")

		self.assertEqual(
			[item["operator"] for item in result["filters"]],
			["iexact", "iexact"],
		)

	@patch("integration.query_parser._get_value_catalog")
	def test_parser_normalizes_model_text_filters(self, get_catalog):
		get_catalog.return_value = {
			"oem": ["NOKIA"],
			"activity_name": ["RET"],
		}
		model_plan = {
			"operation": "count",
			"filters": [
				{"field": "oem", "operator": "exact", "value": "Nokia"},
				{"field": "activity_name", "operator": "exact", "value": "RET"},
			],
		}

		with (
			patch("integration.query_parser._call_llm", return_value=model_plan),
			patch("integration.query_parser.validate_against_question", side_effect=lambda plan, question: plan),
		):
			result = parse_user_query("nokia ret ka count")

		self.assertEqual(
			[item["operator"] for item in result["filters"]],
			["iexact", "iexact"],
		)

	@patch("integration.query_parser._get_value_catalog")
	def test_parser_corrects_model_filter_to_catalog_field(self, get_catalog):
		get_catalog.return_value = {
			"oem": ["SAMSUNG"],
			"activity_name": ["MACRO"],
			"activity_type_siwa": ["INDOOR", "OUTDOOR"],
		}
		model_plan = {
			"operation": "count",
			"filters": [
				{"field": "oem", "operator": "exact", "value": "samsung"},
				{"field": "activity_type_siwa", "operator": "exact", "value": "macro"},
			],
		}

		with (
			patch("integration.query_parser._call_llm", return_value=model_plan),
			patch("integration.query_parser.validate_against_question", side_effect=lambda plan, question: plan),
		):
			result = parse_user_query("samsung macro ka count")

		self.assertEqual(
			result["filters"],
			[
				{"field": "oem", "operator": "iexact", "value": "samsung"},
				{"field": "activity_name", "operator": "iexact", "value": "MACRO"},
			],
		)

	def test_explicit_case_sensitive_filter_is_preserved(self):
		query_plan = {
			"filters": [{"field": "oem", "operator": "exact", "value": "Nokia"}],
		}

		result = _normalize_text_filter_case(query_plan, "case sensitive Nokia")

		self.assertEqual(result["filters"][0]["operator"], "exact")

	@patch("integration.query_parser._get_value_catalog")
	def test_parser_recovers_activity_value_in_ungrouped_count(self, get_catalog):
		get_catalog.return_value = {
			"activity_name": ["RET"],
			"ret": ["RET"],
			"activity_type_siwa": ["RET"],
		}
		model_plan = {
			"operation": "aggregate",
			"aggregation": "count",
			"filters": [],
			"group_by": [],
		}

		with (
			patch("integration.query_parser._call_llm", return_value=model_plan),
			patch("integration.query_parser.validate_against_question", side_effect=lambda plan, question: plan),
		):
			result = parse_user_query("RET ka total count batao")

		self.assertEqual(result["operation"], "count")
		self.assertEqual(
			result["filters"],
			[{"field": "activity_name", "operator": "iexact", "value": "RET"}],
		)

	@patch("integration.query_parser._get_value_catalog")
	def test_parser_adds_activity_value_to_combined_count(self, get_catalog):
		get_catalog.return_value = {
			"circle": ["AP"],
			"activity_name": ["AP", "RET"],
			"ret": ["RET"],
			"activity_type_siwa": ["RET"],
		}
		model_plan = {
			"operation": "aggregate",
			"aggregation": "count",
			"filters": [{"field": "circle", "operator": "iexact", "value": "AP"}],
			"group_by": [],
		}

		with (
			patch("integration.query_parser._call_llm", return_value=model_plan),
			patch("integration.query_parser.validate_against_question", side_effect=lambda plan, question: plan),
		):
			result = parse_user_query("AP mein RET ke kitne records hain?")

		self.assertEqual(
			result["filters"],
			[
				{"field": "circle", "operator": "iexact", "value": "AP"},
				{"field": "activity_name", "operator": "iexact", "value": "RET"},
			],
		)

	@patch("integration.query_parser._get_value_catalog")
	def test_does_not_add_matching_values_from_unrelated_fields(self, get_catalog):
		get_catalog.return_value = {
			"circle": ["AP"],
			"activity_name": ["AP"],
			"oem": ["AP"],
		}
		query_plan = {
			"filters": [{"field": "circle", "operator": "iexact", "value": "AP"}],
		}

		result = _resolve_database_values("AP records", query_plan)

		self.assertEqual(
			result["filters"],
			[{"field": "circle", "operator": "iexact", "value": "AP"}],
		)

	@patch("integration.query_parser._get_value_catalog")
	def test_can_resolve_value_for_field_named_in_question(self, get_catalog):
		get_catalog.return_value = {
			"site_id": ["ABC123"],
			"oem": ["ABC123"],
		}
		query_plan = {"filters": []}

		result = _resolve_database_values("show site ABC123", query_plan)

		self.assertEqual(
			result["filters"],
			[{"field": "site_id", "operator": "iexact", "value": "ABC123"}],
		)

	@patch("integration.query_parser._get_value_catalog")
	def test_can_match_devanagari_database_values(self, get_catalog):
		get_catalog.return_value = {
			"circle": ["उत्तर प्रदेश"],
			"oem": ["उत्तर प्रदेश"],
		}
		query_plan = {"filters": []}

		result = _resolve_database_values("circle उत्तर प्रदेश", query_plan)

		self.assertEqual(
			result["filters"],
			[{"field": "circle", "operator": "iexact", "value": "उत्तर प्रदेश"}],
		)
