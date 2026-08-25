"""Compare two PLAN revisions using the installed fedbpp package."""
import argparse

from fedbpp import Database, Plan, compare_plans

parser = argparse.ArgumentParser()
parser.add_argument("plan_a")
parser.add_argument("plan_b")
parser.add_argument("database")
args = parser.parse_args()

result = compare_plans(Plan.load(args.plan_a), Plan.load(args.plan_b), Database.load(args.database))
print(result["analysisMetadata"]["analysisPolicy"])
