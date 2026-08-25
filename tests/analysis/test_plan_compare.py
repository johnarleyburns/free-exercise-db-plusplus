import csv
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from src.analysis.plan_compare import compare_plans, tidy_rows, write_json, write_tidy_csv

DB = {"metadata": {"schemaVersion": "1.0.0", "converterVersion":"test", "upstream":{"sha256":"abc"}, "setCredits":{"direct":1.0,"indirect":0.5,"stabilizer":0.0}}, "exercises": {
    "press": {"annotation": {"patterns": ["horizontal_push"], "direct": ["chest"], "indirect": ["triceps"], "stabilizers": [], "volumeEligible": True}},
    "row": {"annotation": {"patterns": ["horizontal_pull"], "direct": ["back"], "indirect": ["biceps"], "stabilizers": [], "volumeEligible": True}},
}}

PLAN_A = {"schemaVersion":"0.1.0","planId":"program","revisionId":"r1","cycle":{"lengthDays":7},"sessions":[
 {"planSessionId":"upper","dayOffset":0,"exercises":[{"prescriptionId":"a-press","exerciseId":"press","order":1,"sets":4,"reps":8},{"prescriptionId":"a-row","exerciseId":"row","order":2,"sets":2,"reps":10}]}
]}
PLAN_B = {"schemaVersion":"0.1.0","planId":"program","revisionId":"r2","cycle":{"lengthDays":8},"sessions":[
 {"planSessionId":"upper","dayOffset":0,"exercises":[{"prescriptionId":"b-press","exerciseId":"press","order":1,"sets":3,"reps":10}]},
 {"planSessionId":"pull","dayOffset":3,"exercises":[{"prescriptionId":"b-row","exerciseId":"row","order":1,"sets":4,"reps":8}]}
]}

def test_compare_reports_native_normalized_and_frequency_deltas():
    result = compare_plans(PLAN_A, PLAN_B, DB)
    assert result["plans"]["planB"]["revisionId"] == "r2"
    assert result["analysisMetadata"]["nativePeriodDays"] == {"planA":7,"planB":8}
    assert result["nativeCycle"]["effectiveSets"]["chest"] == {"planA":4.0,"planB":3.0,"delta":-1.0}
    assert result["normalized7Day"]["effectiveSets"]["back"] == {"planA":2.0,"planB":3.5,"delta":1.5}
    assert result["frequency"]["sessions"] == {"planA":1,"planB":2,"delta":1}
    assert result["frequency"]["exercises"]["press"] == {"planA":1.0,"planB":1.0,"delta":0.0}
    assert result["frequency"]["muscles"]["chest"]["exposuresPerNativeCycle"] == {"planA":1,"planB":1,"delta":0}
    assert result["frequency"]["muscles"]["chest"]["normalizedExposuresPer7Days"] == {"planA":1.0,"planB":.875,"delta":-.125}
    assert result["frequency"]["movementPatterns"]["horizontal_pull"]["exposuresPerNativeCycle"] == {"planA":1,"planB":1,"delta":0}
    assert result["analysisMetadata"]["analysisVersion"] == "1.0.0"
    assert result["analysisMetadata"]["analysisPolicy"] == "dbpp-default-volume-v1"
    assert result["analysisMetadata"]["dbConverterVersion"] == "test"
    assert result["analysisMetadata"]["dbUpstreamSha256"] == "abc"
    assert result["analysisMetadata"]["rangePolicy"] == "target-then-min-then-max"
    assert result["analysisMetadata"]["unitPolicy"] == "dbpp-conservative-units-v1"
    assert result["analysisMetadata"]["planSchemaVersions"] == {"planA":"0.1.0","planB":"0.1.0"}

def test_tidy_csv_is_deterministic():
    result = compare_plans(PLAN_A, PLAN_B, DB)
    rows = tidy_rows(result)
    assert rows[0]["kind"] == "volume"
    assert rows == tidy_rows(result)
    with tempfile.TemporaryDirectory() as directory:
        tmp_path = Path(directory)
        output = tmp_path / "comparison.csv"
        write_tidy_csv(result, output)
        parsed = list(csv.DictReader(output.open()))
        assert parsed[0]["kind"] == "volume"
        assert parsed[0]["planA"]
        json_output = tmp_path / "comparison.json"
        write_json(result, json_output)
        assert json_output.read_text().endswith("\n")
