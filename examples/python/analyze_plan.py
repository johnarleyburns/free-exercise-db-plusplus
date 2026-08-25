"""Analyze a PLAN using the installed fedbpp package."""
import argparse

from fedbpp import Database, Plan, analyze_plan

parser = argparse.ArgumentParser()
parser.add_argument("plan")
parser.add_argument("database")
args = parser.parse_args()

result = analyze_plan(Plan.load(args.plan), Database.load(args.database))
print(result["analysisMetadata"]["analysisPolicy"])
print(result["nativeCycle"])
