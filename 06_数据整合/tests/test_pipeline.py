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
        # 通用导入单元测试隔离本轮两条住房挂牌；原补证另有完整回归测试。
        ctx.tables["housing_observations"] = [r for r in ctx.tables["housing_observations"] if not r["id"].startswith("WORK-H")]
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
        expected = {"residences":18,"education_campuses":43,"transport_routes":42,
                    "housing_education_links":41,"accessibility_comparisons":9,"work_evidence":45}
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

    def test_supported_k7_identity_does_not_rehabilitate_bad_route(self):
        x = next(r for r in self.original.tables["entity_crosswalk"] if r["namespace"]=="transport" and r["source_record_id"]=="K7")
        self.assertEqual(x["entity_id"],"CAP-E004-036")
        self.assertEqual(x["match_status"],"matched")
        self.assertIn("WORK-G01",x["match_basis"])
        routes = [r for r in self.original.tables["transport_routes"] if r["destination_legacy_id"]=="K7"]
        self.assertEqual(len(routes),3)
        self.assertEqual({r["origin_legacy_id"]:r["analytical_eligible"] for r in routes},{"D1":True,"D2":True,"D3":False})

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
            self.assertIsNone(row["rent_cny_month"])  # 原两条挂牌和新事实并存，不自动选值。
            self.assertTrue(any(r["id"]=="FACT-TEST-NANGUO-RENT" for r in ctx.tables["housing_observations"]))
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

    def test_work_labels_and_years_are_not_promoted(self):
        rows = {r["id"]:r for r in self.original.tables["work_evidence"]}
        self.assertEqual(rows["WORK-H01"]["verification_status"],"仅索引且版本冲突")
        self.assertEqual(rows["WORK-F09"]["verification_status"],"政策推定")
        self.assertEqual(rows["WORK-F10"]["applicable_year_or_period"],"2024")
        self.assertEqual(rows["WORK-F07"]["subject_ids"],[])
        self.assertEqual(rows["WORK-F05"]["entity_resolution"],"unresolved_institution")

    def test_work_listings_do_not_invent_aggregate(self):
        rows=[r for r in self.original.tables["housing_observations"] if r["residence_id"]=="RES018"]
        self.assertEqual(len(rows),5)
        self.assertEqual({r["value"] for r in rows if r["metric"]=="rent_cny_m2_month"},{69.07,72.5})
        self.assertFalse(any(r["metric"]=="market_reference_sale_cny_m2" for r in rows))
        summary=next(r for r in self.original.tables["residence_cost_summary"] if r["id"]=="RES018")
        self.assertIsNone(summary["sale_reference_cny_m2"])
        self.assertIsNone(summary["rent_cny_month"])

    def test_work_fee_estimate_and_history_never_fill_actual(self):
        rows=[r for r in self.original.tables["education_fees"] if r["id"].startswith("WORK-")]
        self.assertEqual(len(rows),3)
        self.assertTrue(all(not r["actual_charge"] for r in rows))
        self.assertEqual({r["evidence_year"] for r in rows},{2024,2026})
        self.assertTrue(all(r["value"] is None for r in self.original.tables["education_fees"] if r["id"].startswith("FEE-ACTUAL-E004-")))

    def test_work_targeted_routes_preserve_original_sample(self):
        rows=[r for r in self.original.tables["transport_routes"] if r["route_date"]=="2026-11-13"]
        self.assertEqual(len(rows),3)
        self.assertTrue(all(r["distance_m"]>=r["endpoint_chord_m"] for r in rows))
        hb=next(r for r in rows if r["destination_legacy_id"]=="HB")
        self.assertEqual((hb["distance_m"],hb["duration_s"]),(298,238))
        self.assertEqual(len(self.original.tables["walking_sensitivity"]),648)
        self.assertFalse(any("HB" in r["reachable_ids"] or "HW" in r["reachable_ids"] for r in self.original.tables["walking_sensitivity"]))

    def test_work_positions_and_d2_address_roles_stay_separate(self):
        positions={r["id"]:r for r in self.original.tables["positions"]}
        a,b=positions["POS-AMAP-D2"],positions["POS-WORK-D2-MGMT"]
        self.assertNotEqual(a["position_role"],b["position_role"])
        self.assertNotEqual(a["longitude"],b["longitude"])
        self.assertFalse(any(p["gate_verified"] for p in positions.values()))
        for campus in ["CAP-E004-036","CAP-E005-032","CAP-E006-072"]:
            self.assertTrue(next(r["preferred_position_id"] for r in self.original.tables["education_campuses"] if r["id"]==campus))

    def test_work_lease_rules_and_plan_grains(self):
        conditions={r["id"]:r for r in self.original.tables["admission_conditions"]}
        self.assertIn("2025-09-01",conditions["COND-tenant_standard_lease"]["conditions"])
        self.assertIn("2029-08-31",conditions["COND-tianhe_tenant_alternative"]["conditions"])
        self.assertIn("统筹",conditions["COND-relocation_coordinated"]["interpretation_boundary"])
        self.assertEqual(len(self.original.tables["plan_corroboration"]),4)
        self.assertEqual(len(self.original.tables["admission_plans"]),73)

    def test_reference_links_do_not_decide_eligibility(self):
        rows=self.original.tables["housing_education_links"]
        self.assertTrue(all(r["association_role"]=="evidence_lookup_only" for r in rows))
        self.assertFalse(any(r["can_count_eligible_campuses"] or r["can_count_affordable_campuses"] for r in rows))
        self.assertTrue(all(r["household_total_net_cost_cny"] is None for r in rows))
        self.assertTrue(all(not ({"fee_ids","rule_ids","admission_condition_ids"}&set(r)) for r in rows))
        ctx=self.context();ctx.tables["housing_education_links"][0]["can_count_eligible_campuses"]=True
        self.assertFalse(next(r["passed"] for r in validate(ctx)["checks"] if r["id"]=="reference_links_do_not_decide_eligibility"))

    def test_K5_zero_owner_plan(self):
        rows=[r for r in self.original.tables["admission_channel_contexts"] if r["campus_id"]=="CAP-E004-053"]
        self.assertEqual(len(rows),6)
        owner=[r for r in rows if r["channel"]=="affiliated_owner_priority"]
        general=[r for r in rows if r["channel"]=="general_lottery"]
        self.assertTrue(all(r["applicability_status"]=="not_available_in_published_2026_plan" and r["published_owner_children_places"]==0 for r in owner))
        self.assertTrue(all(r["applicability_status"]=="conditional_pathway_reference" for r in general))
        self.assertTrue(all(r["rule_reference_condition_ids"]==["COND-general_lottery"] for r in general))

    def test_fee_layers_never_imply_affordability(self):
        rows={r["id"]:r for r in self.original.tables["education_fees"]}
        self.assertEqual(rows["WORK-F09-conditional_care_fee"]["evidence_layer"],"conditional_estimate")
        self.assertEqual(rows["WORK-F10-historical_care_fee"]["evidence_layer"],"historical_quote")
        self.assertEqual(rows["FEE-F19"]["evidence_layer"],"approved_school_standard")
        self.assertEqual(rows["FEE-F04"]["evidence_layer"],"policy_standard")
        links=self.original.tables["fee_applicability"]
        self.assertTrue(all(r["status"] and not r["usable_for_affordability_count"] for r in links))
        ctx=self.context();ctx.tables["fee_applicability"][0]["status"]=""
        self.assertFalse(next(r["passed"] for r in validate(ctx)["checks"] if r["id"]=="fee_reference_status_complete"))

    def test_route_quality_strata(self):
        from collections import Counter
        rows=self.original.tables["transport_routes"]
        self.assertEqual(Counter(r["analysis_role"] for r in rows),{"ordinary_poi_estimate":39,"supplemental_with_label":2,"excluded":1})
        self.assertTrue(all(r["distance_m"]>=r["endpoint_chord_m"] for r in rows if r["analytical_eligible"]))
        excluded=next(r for r in rows if r["analysis_role"]=="excluded")
        self.assertEqual((excluded["origin_legacy_id"],excluded["destination_legacy_id"]),("D3","K7"))

    def test_warning_years_and_unobserved_outcomes(self):
        rows=self.original.tables["capacity_notices"]
        self.assertEqual({(r["document_year"],r["target_intake_year"]) for r in rows},{(2025,2026),(2026,2027)})
        self.assertTrue(all(r["actual_over_capacity_observed"] is None for r in rows))
        s=next(r for r in self.original.tables["household_scenarios"] if r["origin_legacy_id"]=="D2" and r["profile"]=="Tianhe_hukou_matching_full_home")
        self.assertEqual(s["warning_document_year"],2025)
        self.assertIn("未观察2026实际超额",s["conditions"])

    def test_HK_primary_allocation_not_junior_preferences(self):
        rows=[r for r in self.original.tables["household_scenarios"] if r["profile"]=="Eligible_HK_Macao_points"]
        for r in rows:
            self.assertIn("45",r["conditions"]);self.assertIn("排名",r["conditions"])
            self.assertNotIn("志愿",r["conditions"]);self.assertNotIn("135",r["conditions"]);self.assertNotIn("初中",r["conditions"])
            self.assertEqual(r["actual_admission"],"unobserved")
        contexts=[r for r in self.original.tables["admission_channel_contexts"] if r["channel"]=="district_coordination"]
        self.assertTrue(all(not r["campus_id"] and not r["route_id"] for r in contexts))


if __name__=="__main__":
    unittest.main()
