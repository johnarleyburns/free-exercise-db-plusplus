"""Reviewed relationship decisions kept separate from inference code."""

# These are deliberately small.  The rule engine handles the unambiguous
# lexical cases; this table records taxonomy decisions that deserve review.
FAMILY_OVERRIDES = {
    "Barbell_Bench_Press_-_Medium_Grip": "bench_press",
    "Dumbbell_Bench_Press": "bench_press",
    "Front_Barbell_Squat": "squat",
    "Barbell_Deadlift": "deadlift",
    "Romanian_Deadlift": "romanian_deadlift",
    "Pullups": "pull_up",
    "Chin-Up": "chin_up",
    "Barbell_Curl": "biceps_curl",
    "Triceps_Pushdown": "triceps_extension",
}

# Explicitly excluded from broad families because shared muscles or words do
# not make them the same exercise concept.
EXCLUDED_FAMILY_IDS = {
    "Incline_Bench_Pull": {"bench_press"},
    "Push-Up_to_Side_Plank": {"bench_press"},
    "Upright_Barbell_Row": {"row"},
    "Upright_Cable_Row": {"row"},
    "Good_Morning": {"deadlift", "romanian_deadlift"},
    "Hip_Thrust": {"deadlift"},
    "Kettlebell_Turkish_Get-Up_Squat_style": {"squat"},
    "Squat_Jerk": {"squat"},
    "Jerk_Dip_Squat": {"squat"},
    "Rocky_Pull-Ups_Pulldowns": {"pull_up", "chin_up"},
}
