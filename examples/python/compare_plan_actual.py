"""Compare a PLAN with linked ACTUAL work using the installed fedbpp package."""
import argparse

from fedbpp import Database, Plan, Workout, compare_plan_actual

parser = argparse.ArgumentParser()
parser.add_argument("plan")
parser.add_argument("actual")
parser.add_argument("database")
args = parser.parse_args()

result = compare_plan_actual(Plan.load(args.plan), Workout.load(args.actual), Database.load(args.database))
print(result["matching"]["sessionStatus"])
