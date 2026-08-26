#' Read-only Free Exercise DB++ research helpers.

`%||%` <- function(x, y) if (is.null(x)) y else x

load_database <- function(path) {
  stopifnot(length(path) == 1L)
  document <- jsonlite::fromJSON(path, simplifyVector = FALSE)
  if (is.null(document$exercises) || !is.list(document$exercises)) stop("database is missing exercises")
  structure(list(metadata = document$metadata %||% list(), exercises = document$exercises), class = "fedbpp_database")
}

load_relationships <- function(path) {
  stopifnot(length(path) == 1L)
  document <- jsonlite::fromJSON(path, simplifyVector = FALSE)
  if (is.null(document$families) || is.null(document$relationships)) stop("relationship artifact is missing families or relationships")
  structure(document, class = "fedbpp_relationships")
}

family_for <- function(relationships, exercise_id) {
  rows <- Filter(function(x) identical(x$sourceExerciseId, exercise_id) && identical(x$relationship, "member_of_family"), relationships$relationships)
  if (!length(rows)) return(NULL)
  relationships$families[[rows[[1L]]$familyId]]
}

family_members <- function(relationships, family_id) {
  sort(unique(vapply(Filter(function(x) identical(x$familyId, family_id) && identical(x$relationship, "member_of_family"), relationships$relationships), `[[`, character(1), "sourceExerciseId")))
}

load_workout <- function(path, validate = TRUE) {
  workout <- jsonlite::fromJSON(path, simplifyVector = FALSE)
  if (validate) validate_workout(workout)
  class(workout) <- c("fedbpp_workout", "list")
  workout
}

validate_workout <- function(workout) {
  required <- c("schemaVersion", "sessionId", "startTime", "exercises")
  if (!all(required %in% names(workout))) stop("workout missing required fields")
  if (!identical(workout$schemaVersion, "0.2.0")) stop("unsupported workout schema")
  if (!is.character(workout$sessionId) || !nzchar(workout$sessionId)) stop("sessionId must not be blank")
  if (!is.list(workout$exercises)) stop("exercises must be an array")
  invisible(TRUE)
}

migrate_workout <- function(workout) {
  version <- workout$schemaVersion
  if (identical(version, "0.2.0")) return(workout)
  if (!is.character(version) || !startsWith(version, "0.1.")) stop("unsupported workout schema")
  result <- workout
  result$schemaVersion <- "0.2.0"
  result$exercises <- lapply(result$exercises %||% list(), function(exercise) {
    exercise$laterality <- exercise$laterality %||% "unspecified"
    exercise$sets <- lapply(exercise$sets %||% list(), function(set) {
      set$laterality <- set$laterality %||% NULL
      set
    })
    exercise
  })
  result
}

effective_sets <- function(workout, database) {
  validate_workout(workout)
  rows <- list()
  for (observation in workout$exercises) {
    id <- observation$exerciseId %||% NULL
    if (is.null(id) || is.null(database$exercises[[id]])) next
    exercise <- database$exercises[[id]]
    annotation <- exercise$annotation %||% list()
    if (!isTRUE(annotation$volumeEligible)) next
    counted_types <- c("working", "backoff", "amrap", "drop", "cluster", "rest_pause", "assisted")
    completed <- vapply(observation$sets %||% list(), function(set) isTRUE(set$completed) && (set$setType %||% "working") %in% counted_types, logical(1))
    n <- sum(completed)
    credits <- database$metadata$setCredits %||% list(direct = 1, indirect = 0.5, stabilizer = 0)
    confidence <- annotation$confidence %||% NA_character_
    for (muscle in unlist(annotation$direct %||% list(), use.names = FALSE)) rows[[length(rows) + 1L]] <- data.frame(muscle = muscle, effective_sets = n * credits$direct, credit = credits$direct, exercise_id = id, confidence = confidence, stringsAsFactors = FALSE)
    for (muscle in unlist(annotation$indirect %||% list(), use.names = FALSE)) rows[[length(rows) + 1L]] <- data.frame(muscle = muscle, effective_sets = n * credits$indirect, credit = credits$indirect, exercise_id = id, confidence = confidence, stringsAsFactors = FALSE)
    for (muscle in unlist(annotation$stabilizers %||% list(), use.names = FALSE)) rows[[length(rows) + 1L]] <- data.frame(muscle = muscle, effective_sets = n * credits$stabilizer, credit = credits$stabilizer, exercise_id = id, confidence = confidence, stringsAsFactors = FALSE)
  }
  if (!length(rows)) return(data.frame(muscle = character(), effective_sets = numeric(), credit = numeric(), exercise_id = character(), confidence = character(), stringsAsFactors = FALSE))
  do.call(rbind, rows)
}

workout_observations <- function(workout) {
  validate_workout(workout)
  rows <- lapply(workout$exercises, function(exercise) {
    data.frame(exercise_id = exercise$exerciseId %||% NA_character_, exercise_name = exercise$exerciseName %||% NA_character_, order = exercise$order %||% NA_integer_, set_count = length(exercise$sets %||% list()), stringsAsFactors = FALSE)
  })
  if (!length(rows)) data.frame(exercise_id = character(), exercise_name = character(), order = integer(), set_count = integer(), stringsAsFactors = FALSE) else do.call(rbind, rows)
}

longitudinal_volume <- function(workouts, database) {
  if (inherits(workouts, "fedbpp_workout") || (is.list(workouts) && "schemaVersion" %in% names(workouts))) workouts <- list(workouts)
  rows <- lapply(workouts, function(workout) {
    totals <- effective_sets(workout, database)
    if (!nrow(totals)) return(data.frame(session_id = workout$sessionId %||% NA_character_, start_time = workout$startTime %||% NA_character_, muscle = character(), effective_sets = numeric(), stringsAsFactors = FALSE))
    data.frame(session_id = workout$sessionId %||% NA_character_, start_time = workout$startTime %||% NA_character_, aggregate(totals$effective_sets, list(totals$muscle), sum), stringsAsFactors = FALSE)
  })
  if (!length(rows)) return(data.frame(session_id = character(), start_time = character(), muscle = character(), effective_sets = numeric(), stringsAsFactors = FALSE))
  result <- do.call(rbind, rows); names(result)[3:4] <- c("muscle", "effective_sets"); result
}

# WorkoutIntent 0.1.0 -------------------------------------------------------
# These functions intentionally operate on lists, keeping JSON null versus
# omission observable to research callers while matching the Python oracle's
# resolution statuses and provenance fields.
read_workout_intent <- function(path, validate = TRUE) {
  intent <- jsonlite::fromJSON(path, simplifyVector = FALSE)
  if (validate) validate_workout_intent(intent)
  class(intent) <- c("fedbpp_workout_intent", "list"); intent
}

read_intent_policies <- function() {
  path <- system.file("extdata", "intent-policies.json", package = "fedbpp")
  if (!nzchar(path)) path <- file.path("inst", "extdata", "intent-policies.json")
  jsonlite::fromJSON(path, simplifyVector = FALSE)
}

validate_workout_intent <- function(intent, database = NULL, relationships = NULL) {
  if (!is.list(intent)) return("<root>: must be an object")
  allowed <- c("schemaVersion","intentId","subjectId","goal","schedule","sessionConstraints","environment","equipmentOverrides","exerciseConstraints","preferences","continuity","useHistory","historyWindow","requestedPlanningPolicy","requestedGoalPolicy")
  errors <- setdiff(names(intent), allowed); if (length(errors)) errors <- paste0("<root>: additional property ", errors)
  if (!identical(intent$schemaVersion, "0.1.0")) errors <- c(errors, "schemaVersion: must be 0.1.0")
  schedule <- intent$schedule %||% list(); days <- unique(c(schedule$preferredWeekdays %||% character(), schedule$excludedWeekdays %||% character()))
  if (length(days) && (is.null(schedule$cycleLengthDays) || as.numeric(schedule$cycleLengthDays) != 7)) errors <- c(errors, "schedule weekday fields require cycleLengthDays of 7")
  if (length(intersect(schedule$preferredWeekdays %||% character(), schedule$excludedWeekdays %||% character()))) errors <- c(errors, "schedule: preferredWeekdays and excludedWeekdays conflict")
  if (length(intersect(schedule$preferredDayOffsets %||% integer(), schedule$excludedDayOffsets %||% integer()))) errors <- c(errors, "schedule: preferredDayOffsets and excludedDayOffsets conflict")
  range_errors <- function(r, field) { if (is.null(r)) return(character()); e <- character(); if (!is.null(r$min) && !is.null(r$max) && r$min > r$max) e <- c(e, paste0(field, ": min must not exceed max")); if (!is.null(r$min) && !is.null(r$target) && r$target < r$min) e <- c(e, paste0(field, ": target must not be below min")); if (!is.null(r$max) && !is.null(r$target) && r$target > r$max) e <- c(e, paste0(field, ": target must not exceed max")); e }
  errors <- c(errors, range_errors(schedule$sessionsPerCycle, "schedule.sessionsPerCycle"), range_errors((intent$sessionConstraints %||% list())$exercisesPerSession, "sessionConstraints.exercisesPerSession"))
  constraints <- intent$exerciseConstraints %||% list(); if (length(intersect(unique(base::c(constraints$requiredExerciseIds %||% character(), constraints$lockedExerciseIds %||% character())), constraints$excludedExerciseIds %||% character()))) errors <- base::c(errors, "exerciseConstraints: requiredExerciseIds conflicts with excludedExerciseIds")
  if (length(intersect(constraints$requiredFamilyIds %||% character(), constraints$excludedFamilyIds %||% character()))) errors <- c(errors, "exerciseConstraints: requiredFamilyIds conflicts with excludedFamilyIds")
  for (pair in list(c("preferredExerciseIds", "excludedExerciseIds"), c("avoidedExerciseIds", "excludedExerciseIds"), c("preferredFamilyIds", "excludedFamilyIds"), c("avoidedFamilyIds", "excludedFamilyIds"))) if (length(intersect((intent$preferences %||% list())[[pair[[1L]]]] %||% character(), constraints[[pair[[2L]]]] %||% character()))) errors <- c(errors, paste0("preferences: ", pair[[1L]], " conflicts with ", pair[[2L]]))
  if (identical(intent$goal, "hypertrophy") && identical(intent$requestedGoalPolicy, "general-strength-v1") || identical(intent$goal, "strength") && identical(intent$requestedGoalPolicy, "general-hypertrophy-v1")) errors <- c(errors, "GOAL_POLICY_MISMATCH")
  if (!is.null(intent$requestedGoalPolicy) && !intent$requestedGoalPolicy %in% c("general-hypertrophy-v1", "general-strength-v1")) errors <- c(errors, "requestedGoalPolicy: unknown goal policy")
  if (!is.null(intent$requestedPlanningPolicy) && !intent$requestedPlanningPolicy %in% c("full-body-general-v1", "upper-lower-general-v1")) errors <- c(errors, "requestedPlanningPolicy: unknown planning policy")
  if (!is.null(intent$goal) && !intent$goal %in% c("hypertrophy", "strength", "muscular_endurance", "general_fitness", "skill_practice", "power")) errors <- c(errors, "goal: unsupported value")
  if (!is.null(intent$environment) && !intent$environment %in% c("commercial_gym", "home_gym", "minimal_equipment", "bodyweight_only", "custom")) errors <- c(errors, "environment: unsupported value")
  if (!is.null(intent$continuity) && !intent$continuity %in% c("preserve", "neutral", "vary")) errors <- c(errors, "continuity: unsupported value")
  sort(unique(errors))
}

resolve_intent <- function(intent, db = NULL, profile = NULL, target = NULL, relationships = NULL, history = NULL, as_of = NULL) {
  doc <- if (inherits(intent, "fedbpp_workout_intent")) unclass(intent) else intent
  equipment_overrides <- doc$equipmentOverrides %||% list()
  empty_overrides <- list(goalPolicy = FALSE, planningPolicy = FALSE, target = FALSE, trainingProfile = FALSE, equipmentAdded = character(), equipmentRemoved = character())
  empty <- list(status="invalid", resolvedProfile=NULL, resolvedTarget=NULL, planningPolicy=NULL, goalPolicy=NULL, environmentPolicy=NULL, generationOptions=list(), missingInformation=list(), warnings=character(), conflicts=list(), defaultsApplied=character(), explicitOverrides=empty_overrides, provenance=list(intentSchemaVersion=doc$schemaVersion %||% NULL))
  errors <- validate_workout_intent(doc, db, relationships)
  if (length(errors)) { empty$conflicts <- lapply(errors, function(x) list(code=if (identical(x,"GOAL_POLICY_MISMATCH")) x else "INVALID_INTENT", detail=x)); return(empty) }
  s <- doc$schedule %||% list(); constraints <- doc$exerciseConstraints %||% list(); missing <- list()
  if (is.null(doc$goal)) missing <- c(missing, list(list(field="goal", reason="required_for_goal_policy_resolution")))
  if (is.null(s$cycleLengthDays)) missing <- c(missing, list(list(field="schedule.cycleLengthDays", reason="required_for_schedule_resolution")))
  if (is.null(s$sessionsPerCycle)) missing <- c(missing, list(list(field="schedule.sessionsPerCycle", reason="required_for_schedule_resolution")))
  if (is.null(doc$environment) && (is.null(profile) || is.null(profile$equipment) || !length(profile$equipment))) missing <- c(missing, list(list(field="environmentOrEquipment", reason="required_for_equipment_resolution")))
  if (identical(doc$environment, "home_gym") && (is.null(profile$equipment) || !length(profile$equipment)) && !length(equipment_overrides$addEquipment %||% character())) missing <- c(missing, list(list(field="equipmentOverrides.addEquipment", reason="home_gym_has_no_v1_preset")))
  if (identical(doc$environment, "custom") && (is.null(profile$equipment) || !length(profile$equipment)) && !length(equipment_overrides$addEquipment %||% character())) missing <- c(missing, list(list(field="equipmentOverrides.addEquipment", reason="required_for_custom_environment")))
  if (length(missing)) { empty$status <- "needs_clarification"; empty$missingInformation <- missing; return(empty) }
  goal_id <- doc$requestedGoalPolicy
  if (is.null(goal_id)) goal_id <- switch(doc$goal, hypertrophy="general-hypertrophy-v1", strength="general-strength-v1", NULL)
  if (is.null(goal_id)) { empty$status <- "needs_clarification"; empty$missingInformation <- list(list(field="requestedGoalPolicy", reason="no_default_goal_policy_for_goal")); return(empty) }
  is_strength <- identical(goal_id, "general-strength-v1"); policy_goal <- if (is_strength) "strength" else "hypertrophy"
  if (!identical(doc$goal, policy_goal)) { empty$conflicts <- list(list(code="GOAL_POLICY_MISMATCH", goal=doc$goal, requestedGoalPolicy=goal_id, policyGoal=policy_goal)); return(empty) }
  policies <- read_intent_policies(); goal_policy <- policies$goalPolicies[[goal_id]]; description <- goal_policy$description
  envs <- lapply(policies$environmentPolicies, function(value) list(id=value$policyId, equipment=unlist(value$equipment, use.names=FALSE))); names(envs) <- vapply(envs, function(value) policies$environmentPolicies[[which(vapply(policies$environmentPolicies, function(x) identical(x$policyId, value$id), logical(1)))]]$environment, character(1))
  env <- envs[[doc$environment]]; additions <- sort(unique(equipment_overrides$addEquipment %||% character())); removals <- sort(unique(equipment_overrides$removeEquipment %||% character()))
  profile_has_equipment <- !is.null(profile$equipment) && length(profile$equipment) > 0; base_equipment <- if (profile_has_equipment) profile$equipment else if (!is.null(env)) env$equipment else character(); resolved_equipment <- sort(setdiff(union(base_equipment, additions), removals)); resolved_env <- if (profile_has_equipment) NULL else env
  resolved_profile <- profile %||% list(); resolved_profile$schemaVersion <- resolved_profile$schemaVersion %||% "0.1.0"; resolved_profile$profileId <- resolved_profile$profileId %||% "resolved-profile"; resolved_profile$subjectId <- doc$subjectId %||% resolved_profile$subjectId %||% NULL; resolved_profile$goals <- list(list(type=doc$goal)); resolved_profile$equipment <- resolved_equipment; resolved_profile$exercisePreferences <- resolved_profile$exercisePreferences %||% list(); prefs <- doc$preferences %||% list(); for (key in c("preferredExerciseIds", "avoidedExerciseIds", "preferredFamilyIds", "avoidedFamilyIds")) if (length(prefs[[key]] %||% character())) resolved_profile$exercisePreferences[[key]] <- sort(unique(c(resolved_profile$exercisePreferences[[key]] %||% character(), prefs[[key]])))
  av <- resolved_profile$availability %||% list(); av$cycleLengthDays <- s$cycleLengthDays; av$sessionsPerCycle <- s$sessionsPerCycle; av$preferredDayOffsets <- sort(unique(c(s$preferredDayOffsets %||% integer(), match(s$preferredWeekdays %||% character(), c("monday","tuesday","wednesday","thursday","friday","saturday","sunday"))-1L))); av$preferredDayOffsets <- av$preferredDayOffsets[!is.na(av$preferredDayOffsets)]; av$excludedDayOffsets <- sort(unique(c(s$excludedDayOffsets %||% integer(), match(s$excludedWeekdays %||% character(), c("monday","tuesday","wednesday","thursday","friday","saturday","sunday"))-1L))); av$excludedDayOffsets <- av$excludedDayOffsets[!is.na(av$excludedDayOffsets)]; if (!is.null(doc$sessionConstraints$exercisesPerSession)) av$exercisesPerSession <- doc$sessionConstraints$exercisesPerSession; resolved_profile$availability <- av; resolved_profile$constraints <- resolved_profile$constraints %||% list(); resolved_profile$constraints$excludedExerciseIds <- sort(unique(c(resolved_profile$constraints$excludedExerciseIds %||% character(), constraints$excludedExerciseIds %||% character()))); resolved_profile$constraints$excludedFamilyIds <- sort(unique(c(resolved_profile$constraints$excludedFamilyIds %||% character(), constraints$excludedFamilyIds %||% character())))
  muscles <- goal_policy$muscles; default_target <- list(schemaVersion="0.1.0", targetId=paste0(goal_id,"-default"), periodDays=s$cycleLengthDays, muscles=muscles, notes=description); resolved_target <- merge_target(default_target, target)
  target_errors <- validate_target(resolved_target); if (length(target_errors)) { empty$resolvedTarget <- resolved_target; empty$conflicts <- lapply(target_errors, function(x) list(code="TARGET_OVERRIDE_CONFLICT", detail=x)); return(empty) }
  defaults <- c(if (is.null(doc$requestedGoalPolicy)) "goalPolicy", if (is.null(doc$requestedPlanningPolicy)) "planningPolicy", if (!is.null(resolved_env)) "environmentPolicy")
  options <- list(continuity=doc$continuity %||% "neutral", repDefaults=goal_policy$reps, effortDefaults=goal_policy$effort, requiredFamilyIds=sort(unique(constraints$requiredFamilyIds %||% character())))
  warnings <- character(); if (isTRUE(doc$useHistory) && is.null(history)) warnings <- c(warnings, "useHistory was requested but no history was provided"); if (isTRUE(doc$useHistory) && !is.null(history) && is.null(as_of)) warnings <- c(warnings, "useHistory was requested but as_of is required to derive TrainingState")
  dbmd <- db$metadata %||% list(); rel_version <- if (!is.null(relationships)) relationships$schemaVersion %||% NULL else NULL
  list(status=if(length(defaults)) "resolved_with_defaults" else "resolved", resolvedProfile=resolved_profile, resolvedTarget=resolved_target, planningPolicy=doc$requestedPlanningPolicy %||% "full-body-general-v1", goalPolicy=list(policyId=goal_id, policyVersion="1", description=description), environmentPolicy=if(!is.null(resolved_env)) resolved_env$id else NULL, generationOptions=options, missingInformation=list(), warnings=warnings, conflicts=list(), defaultsApplied=defaults, explicitOverrides=list(goalPolicy=!is.null(doc$requestedGoalPolicy), planningPolicy=!is.null(doc$requestedPlanningPolicy), target=!is.null(target), trainingProfile=!is.null(profile), equipmentAdded=additions, equipmentRemoved=removals), provenance=list(intentSchemaVersion=doc$schemaVersion, goalPolicy=list(policyId=goal_id, policyVersion="1"), environmentPolicy=if(!is.null(resolved_env)) list(policyId=resolved_env$id, policyVersion="1") else NULL, dbSchemaVersion=dbmd$schemaVersion %||% NULL, dbConverterVersion=dbmd$converterVersion %||% NULL, relationshipSchemaVersion=rel_version))
}

generate_plan_from_intent <- function(intent, db, ...) stop("native R plan generation is deferred; use resolve_intent()")

merge_target <- function(default, explicit = NULL) {
  if (is.null(explicit)) return(default)
  result <- default
  merge_section <- function(left, right) { if (is.null(left)) left <- list(); for (key in names(right)) left[[key]] <- if (is.list(right[[key]]) && is.list(left[[key]])) modifyList(left[[key]], right[[key]]) else right[[key]]; left }
  for (key in names(explicit)) {
    if (key %in% c("muscles", "movementPatterns", "families")) result[[key]] <- merge_section(result[[key]], explicit[[key]])
    else if (identical(key, "frequency")) { result$frequency <- result$frequency %||% list(); result$frequency$muscles <- merge_section(result$frequency$muscles, explicit[[key]]$muscles %||% list()) }
    else result[[key]] <- explicit[[key]]
  }
  result
}

validate_target <- function(target) {
  errors <- character(); check <- function(section, values, keys) { if (is.null(values)) return(character()); out <- character(); for (name in names(values)) { r <- values[[name]]; if (!is.null(r[[keys[1]]]) && !is.null(r[[keys[3]]]) && r[[keys[1]]] > r[[keys[3]]]) out <- c(out, paste0(section, ".", name, ": min must not exceed max")); if (!is.null(r[[keys[1]]]) && !is.null(r[[keys[2]]]) && r[[keys[2]]] < r[[keys[1]]]) out <- c(out, paste0(section, ".", name, ": target must not be below min")); if (!is.null(r[[keys[3]]]) && !is.null(r[[keys[2]]]) && r[[keys[2]]] > r[[keys[3]]]) out <- c(out, paste0(section, ".", name, ": target must not exceed max")) }; out }
  errors <- c(errors, check("muscles", target$muscles, c("min", "target", "max")), check("frequency.muscles", (target$frequency %||% list())$muscles, c("min", "target", "max")), check("movementPatterns", target$movementPatterns, c("minimumSets", "targetSets", "maximumSets")), check("families", target$families, c("minimumSets", "targetSets", "maximumSets")))
  sort(unique(errors))
}
