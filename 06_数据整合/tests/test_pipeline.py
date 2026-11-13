import copy
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
ROOT = MODULE.parent
sys.path.insert(0,str(MODULE/"src"))

from liede_pipeline.analysis import build_analysis
from liede_pipeline.common import digest, write_json
from liede_pipeline.coordinates import chord_m, gcj02_to_wgs84, wgs84_to_gcj02
from liede_pipeline.imports import FACT_FIELDS, integrate_feeds, read_feed
from liede_pipeline.pipeline import assemble, build
from liede_pipeline.pipeline import validate_package
from liede_pipeline.validation import check_protected, validate


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = assemble(ROOT,MODULE)

    def context(self):
        ctx = copy.deepcopy(self.original)
        for name in ["verified_facts","import_quarantine","admission_evidence"]:
            ctx.tables[name] = []
        for name in ["housing_observations","education_fees","positions"]:
            ctx.tables[name] = [r for r in ctx.tables[name] if not r["id"].startswith("FACT-")]
        return ctx

    def feed(self,ctx,rows,second=None):
        with tempfile.TemporaryDirectory(prefix="liede-test-facts-") as directory:
            folder = Path(directory)
            for name,items in [("a.csv",rows),("b.csv",second)]:
                if items is None:
                    continue
                with (folder/name).open("w",encoding="utf-8-sig",newline="") as handle:
                    writer = csv.DictWriter(handle,fieldnames=FACT_FIELDS)
                    writer.writeheader()
                    writer.writerows(items)
            integrate_feeds(ctx,folder)

    def fact(self,**changes):
        row = dict.fromkeys(FACT_FIELDS,"")
        row.update(fact_id="TEST-NANGUO-RENT",subject_type="residence",subject_id="RES018",
            predicate="housing_rent_cny_month",value="12345",unit="cny_per_month",reference_period="2026-11",
            source_url="https://example.test/evidence",source_title="Synthetic import fixture",
            source_locator="fixture row 1",evidence_type="test_fixture",verification_status="verified",
            verified_on="2026-11-13",verified_by="unit_test",notes="Not a research observation")
        row.update(changes)
        return row

    def reanalyze(self,ctx):
        for name in ["residence_cost_summary","housing_education_links","evidence_matrix"]:
            ctx.tables[name] = []
        ctx.gaps = []
        build_analysis(ctx)

    def test_complete_baseline_passes(self):
        report = validate(self.original)
        self.assertTrue(report["passed"],[c for c in report["checks"] if not c["passed"]])

    def test_expected_grains(self):
        expected = {"residences":18,"education_campuses":43,"transport_routes":39,
                    "housing_education_links":36,"accessibility_comparisons":9}
        for name,count in expected.items():
            self.assertEqual(len(self.original.tables[name]),count,name)

    def test_campuses_remain_separate(self):
        campuses = {r["id"]:r for r in self.original.tables["education_campuses"]}
        self.assertEqual(campuses["CAP-P04"]["institution_id"],campuses["CAP-P05"]["institution_id"])
        self.assertNotEqual(campuses["CAP-P04"]["id"],campuses["CAP-P05"]["id"])
        self.assertEqual(campuses["CAP-E004-053"]["institution_id"],campuses["CAP-E004-054"]["institution_id"])

    def test_institution_plan_not_copied(self):
        plans = [r for r in self.original.tables["admission_plans"] if r["subject_id"]=="INS-SCH-TH1"]
        self.assertEqual(len(plans),1)
        self.assertEqual(plans[0]["value"],7)
        self.assertEqual(plans[0]["unit"],"class")

    def test_private_plan_names_and_maxima_not_confused(self):
        rows = [r for r in self.original.tables["admission_plans"] if r["metric"]=="maximum_channel_places"]
        self.assertEqual({r["subject_id"]:r["value"] for r in rows},{"CAP-P12":50,"CAP-P13":42})
        self.assertNotIn(21,[r["value"] for r in rows])  # 新蕾五星学校 is a different school.

    def test_transport_only_residence_has_no_invented_housing_crosswalk(self):
        self.assertFalse(any(r["namespace"]=="housing_csv" and r["entity_id"]=="RES018" for r in self.original.tables["entity_crosswalk"]))

    def test_unresolved_k7_never_joins(self):
        x = next(r for r in self.original.tables["entity_crosswalk"] if r["namespace"]=="transport" and r["source_record_id"]=="K7")
        self.assertEqual(x["entity_id"],"")
        self.assertEqual(x["match_status"],"unresolved")
        routes = [r for r in self.original.tables["transport_routes"] if r["destination_legacy_id"]=="K7"]
        self.assertEqual(len(routes),3)
        self.assertTrue(all(not r["analytical_eligible"] for r in routes))

    def test_invalid_length_retained_and_excluded(self):
        r = next(r for r in self.original.tables["transport_routes"] if r["id"]=="ROUTE-D3-K7-20261112-walk")
        self.assertEqual(r["distance_m"],18)
        self.assertGreater(r["endpoint_chord_m"],r["distance_m"])
        self.assertFalse(r["length_check_passed"])

    def test_missing_and_zero_are_distinct(self):
        fees = {r["id"]:r for r in self.original.tables["education_fees"]}
        self.assertIsNone(fees["FEE-ACTUAL-P01"]["value"])
        self.assertEqual(fees["FEE-F06"]["value"],0)
        self.assertIsNone(fees["FEE-F04"]["value"])

    def test_historical_years_retained(self):
        fees = {r["id"]:r for r in self.original.tables["education_fees"]}
        self.assertEqual(fees["FEE-F17"]["evidence_year"],2020)
        self.assertEqual(fees["FEE-F18"]["evidence_year"],2022)
        primary = next(r for r in self.original.tables["education_campuses"] if r["id"]=="CAP-P01")
        self.assertEqual(primary["address_year"],"2022")
        self.assertEqual(primary["admission_year"],2026)

    def test_gcj_conversion_and_numerical_inverse(self):
        for lon,lat in [(113.336127,23.113409),(113.344585,23.114459)]:
            x,y = gcj02_to_wgs84(lon,lat)
            self.assertGreater(chord_m(lon,lat,x,y),100)
            a,b = wgs84_to_gcj02(x,y)
            self.assertLess(chord_m(lon,lat,a,b),.02)

    def test_scope_failure_is_detected(self):
        ctx = self.context()
        ctx.tables["education_campuses"][0]["stage"] = "junior"
        report = validate(ctx)
        self.assertFalse(next(c for c in report["checks"] if c["id"]=="primary_kindergarten_only")["passed"])

    def test_crosswalk_ambiguity_is_detected(self):
        ctx = self.context()
        r = dict(ctx.tables["entity_crosswalk"][0],id="DUPLICATE-MAPPING",entity_id="RES018")
        ctx.tables["entity_crosswalk"].append(r)
        report = validate(ctx)
        self.assertFalse(next(c for c in report["checks"] if c["id"]=="crosswalk_single_target")["passed"])

    def test_valid_fact_updates_missing_derived_cost(self):
        ctx = self.context()
        self.feed(ctx,[self.fact()])
        self.reanalyze(ctx)
        r = next(r for r in ctx.tables["residence_cost_summary"] if r["id"]=="RES018")
        self.assertEqual(r["rent_cny_month"],12345)
        self.assertEqual(len(ctx.tables["import_quarantine"]),0)

    def test_complete_rebuild_with_external_feed(self):
        with tempfile.TemporaryDirectory(prefix="liede-import-e2e-") as directory:
            folder = Path(directory)
            inbox = folder/"inbox"
            inbox.mkdir()
            with (inbox/"facts.csv").open("w",encoding="utf-8-sig",newline="") as handle:
                writer = csv.DictWriter(handle,fieldnames=FACT_FIELDS)
                writer.writeheader()
                writer.writerow(self.fact())
            ctx,report,_ = build(ROOT,MODULE,folder/"output",inbox,False)
            self.assertTrue(report["passed"])
            row = next(r for r in ctx.tables["residence_cost_summary"] if r["id"]=="RES018")
            self.assertEqual(row["rent_cny_month"],12345)
            self.assertTrue(all(c["passed"] for c in validate_package(folder/"output")))

    def test_unknown_entity_is_not_fuzzy_matched(self):
        ctx = self.context()
        self.feed(ctx,[self.fact(subject_id="南国花园")])
        self.assertEqual(ctx.tables["import_quarantine"][0]["reason"],"unresolved_entity_id")
        self.assertFalse(any(r["id"]=="FACT-TEST-NANGUO-RENT" for r in ctx.tables["housing_observations"]))

    def test_bad_numeric_values_are_quarantined(self):
        for value in ["NaN","inf","-1",""]:
            with self.subTest(value=value):
                ctx = self.context()
                self.feed(ctx,[self.fact(value=value)])
                self.assertEqual(len(ctx.tables["import_quarantine"]),1)

    def test_wrong_unit_is_quarantined(self):
        ctx = self.context()
        self.feed(ctx,[self.fact(unit="cny_per_m2_month")])
        self.assertEqual(ctx.tables["import_quarantine"][0]["reason"],"predicate_subject_or_unit_mismatch")

    def test_junior_fact_is_quarantined(self):
        ctx = self.context()
        self.feed(ctx,[self.fact(stage="junior")])
        self.assertEqual(ctx.tables["import_quarantine"][0]["reason"],"out_of_scope_stage")

    def test_unverified_fact_is_quarantined(self):
        ctx = self.context()
        self.feed(ctx,[self.fact(verification_status="pending")])
        self.assertEqual(ctx.tables["import_quarantine"][0]["reason"],"verification_not_confirmed")

    def test_duplicate_identical_fact_is_idempotent(self):
        ctx = self.context()
        r = self.fact()
        self.feed(ctx,[r],[r])
        facts = [x for x in ctx.tables["verified_facts"] if x["fact_id"]==r["fact_id"]]
        self.assertEqual(len(facts),1)
        self.assertEqual(facts[0]["duplicate_copies_ignored"],1)

    def test_conflicting_duplicate_fact_ids_quarantine_both(self):
        ctx = self.context()
        self.feed(ctx,[self.fact()],[self.fact(value="9999")])
        self.assertEqual(len(ctx.tables["import_quarantine"]),2)
        self.assertTrue(all(r["reason"]=="conflicting_duplicate_fact_id" for r in ctx.tables["import_quarantine"]))

    def test_conflicting_feed_rebuilds_without_duplicate_gap_ids(self):
        with tempfile.TemporaryDirectory(prefix="liede-conflict-e2e-") as directory:
            folder = Path(directory)
            inbox = folder/"inbox"
            inbox.mkdir()
            with (inbox/"facts.csv").open("w",encoding="utf-8-sig",newline="") as handle:
                writer = csv.DictWriter(handle,fieldnames=FACT_FIELDS)
                writer.writeheader()
                writer.writerows([self.fact(),self.fact(value="9999")])
            ctx,report,_ = build(ROOT,MODULE,folder/"output",inbox,False)
            self.assertTrue(report["passed"])
            self.assertEqual(len(ctx.tables["import_quarantine"]),2)
            gaps = [g for g in ctx.gaps if g["code"]=="IMPORT_REVIEW"]
            self.assertEqual(len(gaps),1)
            self.assertEqual(gaps[0]["occurrences"],2)

    def test_quarantine_ids_do_not_depend_on_checkout_path(self):
        a,b = self.context(),self.context()
        self.feed(a,[self.fact(subject_id="unresolved")])
        self.feed(b,[self.fact(subject_id="unresolved")])
        self.assertEqual(a.tables["import_quarantine"][0]["id"],b.tables["import_quarantine"][0]["id"])

    def test_conflicting_price_is_not_averaged_or_overwritten(self):
        ctx = self.context()
        self.feed(ctx,[self.fact(subject_id="RES015",predicate="housing_reference_price_cny_m2",
            value="99999",unit="cny_per_m2",reference_period="2026-09")])
        self.reanalyze(ctx)
        r = next(r for r in ctx.tables["residence_cost_summary"] if r["id"]=="RES015")
        self.assertIsNone(r["sale_reference_cny_m2"])
        self.assertEqual(r["sale_status"],"conflicting_or_multiple_periods")
        self.assertTrue(any(x["value"]==102011 for x in ctx.tables["housing_observations"] if x["residence_id"]=="RES015"))

    def test_coordinate_conflict_preserves_existing_default(self):
        ctx = self.context()
        home = next(r for r in ctx.tables["residences"] if r["id"]=="RES003")
        old = home["preferred_position_id"]
        self.feed(ctx,[self.fact(subject_id="RES003",predicate="coordinate_wgs84",unit="degrees",
            value=json.dumps(dict(longitude=113.32,latitude=23.12,position_role="development_reference")))])
        self.assertEqual(home["preferred_position_id"],old)
        pos = next(p for p in ctx.tables["positions"] if p["id"]=="FACT-TEST-NANGUO-RENT")
        self.assertEqual(pos["entity_id"],"")
        self.assertEqual(pos["candidate_entity_id"],"RES003")

    def test_source_id_url_conflict_is_quarantined(self):
        ctx = self.context()
        self.feed(ctx,[self.fact(source_id="E002")])
        self.assertIn("Source ID/URL conflict",ctx.tables["import_quarantine"][0]["reason"])

    def test_estimated_fee_is_not_an_actual_charge_record(self):
        ctx = self.context()
        self.feed(ctx,[self.fact(subject_type="campus",subject_id="CAP-E004-052",stage="kindergarten",
            predicate="care_fee_cny_month",value="100",unit="cny_per_person_month",evidence_type="estimated")])
        r = next(r for r in ctx.tables["education_fees"] if r["id"]=="FACT-TEST-NANGUO-RENT")
        self.assertFalse(r["actual_charge"])

    def test_reference_period_is_not_source_publication_date(self):
        ctx = self.context()
        self.feed(ctx,[self.fact()])
        source = next(r for r in ctx.source_manager.rows.values() if r["url"]=="https://example.test/evidence")
        self.assertEqual(source["document_date"],"")

    def test_output_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p/"data.csv").write_text("a,b\n")
            write_json(p/"run_manifest.json",{"artifact_sha256":{"data.csv":digest(p/"data.csv")}})
            self.assertTrue(validate_package(p)[0]["passed"])
            (p/"data.csv").write_text("tampered\n")
            self.assertFalse(validate_package(p)[0]["passed"])

    def test_missing_csv_columns_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"bad.csv"
            p.write_text("fact_id,value\ntest,3\n")
            with self.assertRaises(ValueError):
                read_feed(p)

    def test_short_csv_row_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"short.csv"
            p.write_text(",".join(FACT_FIELDS)+"\nonly-one-cell\n")
            with self.assertRaises(ValueError):
                read_feed(p)

    def test_protected_file_change_detected_without_touching_repository(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            module = root/"integration"
            (module/".state").mkdir(parents=True)
            original = root/"original.csv"
            original.write_text("untouched\n")
            write_json(module/".state/protected_files.json",{"original.csv":digest(original)})
            self.assertTrue(check_protected(root,module)["passed"])
            original.write_text("changed test fixture\n")
            self.assertFalse(check_protected(root,module)["passed"])


if __name__=="__main__":
    unittest.main()
