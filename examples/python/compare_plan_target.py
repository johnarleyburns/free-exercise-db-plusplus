"""Compare a PLAN with a TARGET using the installed fedbpp package."""
import argparse

from fedbpp import Database, Plan, VolumeTarget, compare_to_targets

parser = argparse.ArgumentParser()
parser.add_argument("plan")
parser.add_argument("target")
parser.add_argument("database")
args = parser.parse_args()

result = compare_to_targets(Plan.load(args.plan), VolumeTarget.load(args.target), Database.load(args.database))
print(result["muscles"])
