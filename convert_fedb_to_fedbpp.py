#!/usr/bin/env python3
"""
Convert yuhonas/free-exercise-db combined exercises JSON into Free Exercise DB++.

v0.1 goals:
- deterministic and reviewable;
- preserve original source record;
- distinguish direct, indirect, and stabilizer roles;
- flag uncertain fallback classifications;
- validate against JSON Schema optionally.

This is deliberately conservative. A low-confidence mapping is preferable to
silently pretending that a complex exercise has been biomechanically resolved.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import os
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.3.0"
CONVERTER_VERSION = "0.8.0"
UPSTREAM_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"

MUSCLES = [
    "abdominals","abductors","adductors","biceps","calves","chest",
    "forearms","glutes","hamstrings","lats","lower_back","middle_back",
    "neck","quadriceps","shoulders","traps","triceps",
    "tibialis","rotator_cuff","hip_flexors",
]

SET_CREDITS = {"direct": 1.0, "indirect": 0.5, "stabilizer": 0.0}

EVIDENCE_REFERENCES = {'bench_systematic_review_2017': {'title': 'A systematic review of surface electromyography analyses of the bench press movement task', 'type': 'systematic_review', 'pmid': '28170449', 'doi': '10.1371/journal.pone.0171632', 'url': 'https://pubmed.ncbi.nlm.nih.gov/28170449/'}, 'bench_inclination_2020': {'title': 'Effect of Five Bench Inclinations on EMG Activity during Bench Press', 'type': 'experimental', 'pmid': '33049982', 'url': 'https://pubmed.ncbi.nlm.nih.gov/33049982/'}, 'deadlift_systematic_review_2020': {'title': 'Electromyographic activity in deadlift exercise and its variants. A systematic review', 'type': 'systematic_review', 'pmid': '32107499', 'doi': '10.1371/journal.pone.0229507', 'url': 'https://pubmed.ncbi.nlm.nih.gov/32107499/'}, 'hip_thrust_systematic_review_2019': {'title': 'Barbell Hip Thrust, Muscular Activation and Performance: A Systematic Review', 'type': 'systematic_review', 'pmid': '31191088', 'url': 'https://pubmed.ncbi.nlm.nih.gov/31191088/'}, 'glute_strength_review_2020': {'title': 'Gluteus Maximus Activation during Common Strength and Hypertrophy Exercises: A Systematic Review', 'type': 'systematic_review', 'pmid': '32132843', 'url': 'https://pubmed.ncbi.nlm.nih.gov/32132843/'}, 'pullup_emg_2017': {'title': 'Electromyographical Comparison of a Traditional, Suspension Device, and Towel Pull-Up', 'type': 'experimental', 'pmid': '28828073', 'url': 'https://pubmed.ncbi.nlm.nih.gov/28828073/'}, 'hamstring_exercises_2014': {'title': 'Muscle activation during various hamstring exercises', 'type': 'experimental', 'pmid': '24149748', 'url': 'https://pubmed.ncbi.nlm.nih.gov/24149748/'}, 'hip_abduction_review_2015': {'title': 'An examination of gluteal muscle activity associated with dynamic hip abduction and hip external rotation exercise: a systematic review', 'type': 'systematic_review', 'pmid': '26491608', 'url': 'https://pubmed.ncbi.nlm.nih.gov/26491608/'}, 'olympic_emg_2026': {'title': 'Olympic weightlifting neuromuscular activation study', 'type': 'experimental', 'pmid': '41352184', 'url': 'https://pubmed.ncbi.nlm.nih.gov/41352184/'}, 'olympic_position_2023': {'title': 'Olympic weightlifting derivatives / position statement evidence', 'type': 'review_or_position', 'pmid': '36952649', 'url': 'https://pubmed.ncbi.nlm.nih.gov/36952649/'}, 'olympic_kinetics_2012': {'title': 'Olympic lifting phase biomechanics', 'type': 'experimental', 'pmid': '21975459', 'url': 'https://pubmed.ncbi.nlm.nih.gov/21975459/'}, 'kettlebell_emg_2017': {'title': 'Kettlebell swing, clean, and snatch muscle activation', 'type': 'experimental', 'pmid': '28394829', 'url': 'https://pubmed.ncbi.nlm.nih.gov/28394829/'}, 'kettlebell_swing_2012': {'title': 'Kettlebell swing biomechanics and muscle activation', 'type': 'experimental', 'pmid': '21997449', 'url': 'https://pubmed.ncbi.nlm.nih.gov/21997449/'}, 'atlas_stone_2021': {'title': 'Atlas stone biomechanics', 'type': 'experimental', 'pmid': '34557349', 'url': 'https://pubmed.ncbi.nlm.nih.gov/34557349/'}, 'tire_flip_2010': {'title': 'Tire flip biomechanics', 'type': 'experimental', 'pmid': '20386131', 'url': 'https://pubmed.ncbi.nlm.nih.gov/20386131/'}, 'strongman_trunk_2009': {'title': 'Strongman trunk loading', 'type': 'experimental', 'pmid': '19528856', 'url': 'https://pubmed.ncbi.nlm.nih.gov/19528856/'}, 'strongman_review_2019': {'title': 'Strongman exercise systematic review', 'type': 'systematic_review', 'pmid': '31820223', 'url': 'https://pubmed.ncbi.nlm.nih.gov/31820223/'}, 'fractional_sets_meta_regression_2025': {'title': 'The Resistance Training Dose Response: Meta-Regressions Exploring Weekly Volume and Frequency', 'type': 'meta_regression', 'pmid': '41343037', 'url': 'https://pubmed.ncbi.nlm.nih.gov/41343037/'}, 'shoulder_press_emg_2013': {'title': 'Effects of body position and loading modality on muscle activity and strength in shoulder presses', 'type': 'experimental', 'pmid': '23096062', 'doi': '10.1519/JSC.0b013e318276b873', 'url': 'https://pubmed.ncbi.nlm.nih.gov/23096062/'}, 'shoulder_training_emg_2012': {'title': 'Evaluation of muscle activity during a standardized shoulder resistance training bout in novice individuals', 'type': 'experimental', 'pmid': '22067242', 'doi': '10.1519/JSC.0b013e31823f29d9', 'url': 'https://pubmed.ncbi.nlm.nih.gov/22067242/'}, 'lateral_raise_emg_2020': {'title': 'An Electromyographic Analysis of Lateral Raise Variations and Frontal Raise in Competitive Bodybuilders', 'type': 'experimental', 'pmid': '32824894', 'url': 'https://pubmed.ncbi.nlm.nih.gov/32824894/'}, 'biceps_curl_emg_2013': {'title': 'Effect of the shoulder position on the biceps brachii EMG in different dumbbell curls', 'type': 'experimental', 'pmid': '24150552', 'url': 'https://pubmed.ncbi.nlm.nih.gov/24150552/'}, 'curl_variants_emg_2018': {'title': 'Differences in electromyographic activity of biceps brachii and brachioradialis while performing three variants of curl', 'type': 'experimental', 'pmid': '30013836', 'doi': '10.7717/peerj.5165', 'url': 'https://pubmed.ncbi.nlm.nih.gov/30013836/'}, 'triceps_extension_emg_2017': {'title': 'Effect of shoulder position on triceps brachii heads activity in dumbbell elbow extension exercises', 'type': 'experimental', 'pmid': '28677940', 'doi': '10.23736/S0022-4707.17.06849-9', 'url': 'https://pubmed.ncbi.nlm.nih.gov/28677940/'}, 'leg_extension_hypertrophy_2021': {'title': 'Drop-Set Training Elicits Differential Increases in Non-Uniform Hypertrophy of the Quadriceps in Leg Extension Exercise', 'type': 'training_intervention', 'pmid': '34564324', 'url': 'https://pubmed.ncbi.nlm.nih.gov/34564324/'}, 'leg_extension_comparison_2026': {'title': 'Comparison of Muscle Hypertrophy and Strength Adaptations Induced by Back Squat and Leg Extension Resistance Exercises', 'type': 'training_intervention', 'pmid': '41379528', 'url': 'https://pubmed.ncbi.nlm.nih.gov/41379528/'}, 'crunch_loaded_emg_2009': {'title': 'EMG activation of abdominal muscles in the crunch exercise performed with different external loads', 'type': 'experimental', 'pmid': '19376473', 'doi': '10.1016/j.ptsp.2009.01.001', 'url': 'https://pubmed.ncbi.nlm.nih.gov/19376473/'}, 'situp_curlup_emg_2008': {'title': 'The effects of different sit- and curl-up positions on activation of abdominal and hip flexor musculature', 'type': 'experimental', 'pmid': '18923563', 'doi': '10.1139/H08-061', 'url': 'https://pubmed.ncbi.nlm.nih.gov/18923563/'}, 'trunk_rotation_rct_2021': {'title': 'The influence of rotational movement exercise on the abdominal muscle thickness and trunk mobility', 'type': 'randomized_controlled_trial', 'pmid': '34391272', 'url': 'https://pubmed.ncbi.nlm.nih.gov/34391272/'}, 'flexion_rotation_emg_2020': {'title': 'Electromyographic and Kinematic Analysis of the Flexion-Rotation Trunk Test', 'type': 'experimental', 'pmid': '28796125', 'doi': '10.1519/JSC.0000000000002168', 'url': 'https://pubmed.ncbi.nlm.nih.gov/28796125/'}, 'bridge_stabilization_emg_2012': {'title': 'Trunk muscle activation during stabilization exercises with single and double leg support', 'type': 'experimental', 'pmid': '22436839', 'doi': '10.1016/j.jelekin.2012.02.017', 'url': 'https://pubmed.ncbi.nlm.nih.gov/22436839/'}, 'bridge_surface_emg_2013': {'title': 'Abdominal muscle EMG-activity during bridge exercises on stable and unstable surfaces', 'type': 'experimental', 'pmid': '24268641', 'doi': '10.1016/j.ptsp.2013.09.003', 'url': 'https://pubmed.ncbi.nlm.nih.gov/24268641/'}, 'side_bridge_oblique_emg_2020': {'title': 'Surface Electromyography of the Internal and External Oblique Muscles During Isometric Tasks Targeting the Lateral Trunk', 'type': 'experimental', 'pmid': '32369764', 'url': 'https://pubmed.ncbi.nlm.nih.gov/32369764/'}, 'side_bridge_asymmetry_2022': {'title': 'Side-To-Side Difference in Electromyographic Activity of Abdominal Muscles during Asymmetric Exercises', 'type': 'experimental', 'pmid': '36523892', 'url': 'https://pubmed.ncbi.nlm.nih.gov/36523892/'}, 'pullover_emg_2011': {'title': 'Effects of the pullover exercise on the pectoralis major and latissimus dorsi muscles as evaluated by EMG', 'type': 'experimental', 'pmid': '21975179', 'doi': '10.1123/jab.27.4.380', 'url': 'https://pubmed.ncbi.nlm.nih.gov/21975179/'}, 'upright_row_grip_emg_2012': {'title': 'Effect of grip width on electromyographic activity during the upright row', 'type': 'experimental', 'pmid': '22362088', 'url': 'https://pubmed.ncbi.nlm.nih.gov/22362088/'}, 'hip_flexor_systematic_review_2024': {'title': 'Hip Flexor Muscle Activation During Common Rehabilitation and Strength Exercises', 'type': 'systematic_review', 'pmid': '39518756', 'url': 'https://pubmed.ncbi.nlm.nih.gov/39518756/'}, 'psoas_aslr_emg_2010': {'title': 'Is the psoas a hip flexor in the active straight leg raise?', 'type': 'experimental', 'pmid': '20625774', 'url': 'https://pubmed.ncbi.nlm.nih.gov/20625774/'}, 'external_rotation_emg_2004': {'title': 'Electromyographic analysis of the rotator cuff and deltoid musculature during common shoulder external rotation exercises', 'type': 'experimental', 'pmid': '15296366', 'doi': '10.2519/jospt.2004.34.7.385', 'url': 'https://pubmed.ncbi.nlm.nih.gov/15296366/'}, 'external_rotation_roles_2012': {'title': 'Rotator cuff muscles perform different functional roles during shoulder external rotation exercises', 'type': 'experimental', 'pmid': '22836526', 'doi': '10.1002/ca.22128', 'url': 'https://pubmed.ncbi.nlm.nih.gov/22836526/'}, 'internal_rotation_emg_2003': {'title': 'Electromyographic analysis of internal rotational motion of the shoulder in various arm positions', 'type': 'experimental', 'pmid': '14564277', 'doi': '10.1016/S1058-2746(03)00169-1', 'url': 'https://pubmed.ncbi.nlm.nih.gov/14564277/'}, 'subscapularis_exercise_2003': {'title': 'Subscapularis muscle activity during selected rehabilitation exercises', 'type': 'experimental', 'pmid': '12531769', 'url': 'https://pubmed.ncbi.nlm.nih.gov/12531769/'}, 'back_extension_roman_chair_2014': {'title': 'Effects of hand and knee positions on muscular activity during trunk extension exercise with the Roman chair', 'type': 'experimental', 'pmid': '25245250', 'url': 'https://pubmed.ncbi.nlm.nih.gov/25245250/'}, 'back_extension_comparison_2021': {'title': 'Comparison of Muscle Activity in Three Single-Joint, Hip Extension Exercises in Resistance-Trained Women', 'type': 'experimental', 'pmid': '33948095', 'url': 'https://pubmed.ncbi.nlm.nih.gov/33948095/'}, 'calf_raise_hypertrophy_2023': {'title': 'Triceps surae muscle hypertrophy is greater after standing versus seated calf-raise training', 'type': 'training_intervention', 'pmid': '38156065', 'doi': '10.3389/fphys.2023.1272106', 'url': 'https://pubmed.ncbi.nlm.nih.gov/38156065/'}, 'calf_raise_swelling_2023': {'title': 'Muscle Swelling of the Triceps Surae in Response to Straight-Leg and Bent-Leg Calf Raise Exercises in Young Women', 'type': 'experimental', 'pmid': '37015022', 'doi': '10.1519/JSC.0000000000004491', 'url': 'https://pubmed.ncbi.nlm.nih.gov/37015022/'}, 'calf_raise_emg_2021': {'title': 'Myoelectric activity of the gastrocnemius during plantar flexion in a standing versus seated position', 'type': 'experimental', 'pmid': '33992275', 'doi': '10.1016/j.jbmt.2020.09.003', 'url': 'https://pubmed.ncbi.nlm.nih.gov/33992275/'}, 'strongman_trunk_events_2009': {'title': 'Comparison of different strongman events: trunk muscle activation and lumbar spine motion, load, and stiffness', 'type': 'experimental', 'pmid': '19528856', 'doi': '10.1519/JSC.0b013e318198f8f7', 'url': 'https://pubmed.ncbi.nlm.nih.gov/19528856/'}, 'sled_push_emg_2021': {'title': 'Electromyography, Stiffness and Kinematics of Resisted Sprint Training Using Different Load Conditions', 'type': 'experimental', 'pmid': '34833557', 'url': 'https://pubmed.ncbi.nlm.nih.gov/34833557/'}, 'battle_rope_emg_2015': {'title': 'Muscle Activity During Unilateral vs. Bilateral Battle Rope Exercises', 'type': 'experimental', 'pmid': '25853917', 'url': 'https://pubmed.ncbi.nlm.nih.gov/25853917/'}, 'battle_rope_wbv_emg_2015': {'title': 'The addition of synchronous whole-body vibration to battling rope exercise increases skeletal muscle activity', 'type': 'experimental', 'pmid': '26350942', 'url': 'https://pubmed.ncbi.nlm.nih.gov/26350942/'}, 'pallof_press_postural_2025': {'title': 'Effect of Body Position and Support Surface on the Postural Control Challenge During the Pallof Press Exercise', 'type': 'experimental', 'pmid': '40005429', 'doi': '10.3390/medicina61020312', 'url': 'https://pubmed.ncbi.nlm.nih.gov/40005429/'}, 'inverted_row_emg_2015': {'title': 'Activation of Spinal Stabilizers and Shoulder Complex Muscles During an Inverted Row Using a Portable Pull-up Device and Body Weight Resistance', 'type': 'experimental', 'pmid': '26422610', 'url': 'https://pubmed.ncbi.nlm.nih.gov/26422610/'}, 'prone_barbell_row_emg_2025': {'title': 'Impact of different ranges of motion in the prone barbell row on muscle excitation', 'type': 'experimental', 'pmid': '40513198', 'doi': '10.1016/j.jelekin.2025.103025', 'url': 'https://pubmed.ncbi.nlm.nih.gov/40513198/'}, 'suspension_row_emg_2020': {'title': 'Recruitment of Shoulder Complex and Torso Stabilizer Muscles With Rowing Exercises Using a Suspension Strap Training System', 'type': 'experimental', 'pmid': '32940548', 'url': 'https://pubmed.ncbi.nlm.nih.gov/32940548/'}, 'neck_isometric_emg_2002': {'title': 'Electromyography of superficial cervical muscles with exertion in the sagittal, coronal and oblique planes', 'type': 'experimental', 'pmid': '11931061', 'url': 'https://pubmed.ncbi.nlm.nih.gov/11931061/'}, 'neck_conditioning_emg_2008': {'title': 'An electromyographic comparison of neck conditioning exercises in healthy controls', 'type': 'experimental', 'pmid': '18550959', 'url': 'https://pubmed.ncbi.nlm.nih.gov/18550959/'}, 'forearm_pronation_supination_emg_2026': {'title': 'An Electromyographic Study Comparing Muscle Function During Supination and Pronation of the Forearm', 'type': 'experimental', 'pmid': '41674760', 'doi': '10.7759/cureus.101255', 'url': 'https://pubmed.ncbi.nlm.nih.gov/41674760/'}, 'forearm_grip_emg_2019': {'title': 'The influence of simultaneous handgrip and wrist force on forearm muscle activity', 'type': 'experimental', 'pmid': '30822679', 'doi': '10.1016/j.jelekin.2019.02.004', 'url': 'https://pubmed.ncbi.nlm.nih.gov/30822679/'}, 'power_grip_emg_2015': {'title': 'Evaluating protocols for normalizing forearm electromyograms during power grip', 'type': 'experimental', 'pmid': '26589588', 'doi': '10.1016/j.jelekin.2015.10.014', 'url': 'https://pubmed.ncbi.nlm.nih.gov/26589588/'}}

PATTERN_EVIDENCE = {'horizontal_press': {'status': 'supported', 'summary': 'Bench-press literature supports pectoralis major and triceps as major prime movers with anterior deltoid contribution; inclination changes relative contribution.', 'references': ['bench_systematic_review_2017', 'bench_inclination_2020']}, 'incline_press': {'status': 'supported', 'summary': 'Bench-press literature supports pectoralis major and triceps as major prime movers with anterior deltoid contribution; inclination changes relative contribution.', 'references': ['bench_systematic_review_2017', 'bench_inclination_2020']}, 'decline_press': {'status': 'supported', 'summary': 'Bench-press literature supports pectoralis major and triceps as major prime movers with anterior deltoid contribution; inclination changes relative contribution.', 'references': ['bench_systematic_review_2017', 'bench_inclination_2020']}, 'vertical_press': {'status': 'supported', 'summary': 'Shoulder-press EMG directly supports anterior/medial deltoid and triceps involvement across seated/standing and barbell/dumbbell variants.', 'references': ['shoulder_press_emg_2013']}, 'horizontal_press_triceps_bias': {'status': 'supported', 'summary': 'Bench-press literature supports pectoralis major and triceps as major prime movers with anterior deltoid contribution; inclination changes relative contribution.', 'references': ['bench_systematic_review_2017', 'bench_inclination_2020']}, 'dip_chest_bias': {'status': 'supported', 'summary': 'Bench-press literature supports pectoralis major and triceps as major prime movers with anterior deltoid contribution; inclination changes relative contribution.', 'references': ['bench_systematic_review_2017', 'bench_inclination_2020']}, 'dip_triceps_bias': {'status': 'supported', 'summary': 'Bench-press literature supports pectoralis major and triceps as major prime movers with anterior deltoid contribution; inclination changes relative contribution.', 'references': ['bench_systematic_review_2017', 'bench_inclination_2020']}, 'horizontal_pull': {'status': 'supported', 'summary': 'Direct row-family EMG evidence across inverted, prone/barbell and suspension rows supports latissimus dorsi and mid/lower trapezius as major back contributors, with biceps and posterior deltoid also substantially recruited. DB++ retains biceps and shoulders as indirect because their relative contribution varies materially by row variant.', 'references': ['inverted_row_emg_2015', 'prone_barbell_row_emg_2025', 'suspension_row_emg_2020']}, 'vertical_pull': {'status': 'supported', 'summary': 'Direct pull-up EMG evidence supports latissimus dorsi and biceps as major contributors, with posterior shoulder and mid-trapezius involvement; this directly supports the vertical-pull family.', 'references': ['pullup_emg_2017']}, 'shrug': {'status': 'supported', 'summary': 'A standardized resistance-training EMG study directly measured reverse fly and shrug recruitment of deltoid/trapezius regions.', 'references': ['shoulder_training_emg_2012']}, 'reverse_fly': {'status': 'supported', 'summary': 'A standardized resistance-training EMG study directly measured reverse fly and shrug recruitment of deltoid/trapezius regions.', 'references': ['shoulder_training_emg_2012']}, 'shoulder_abduction': {'status': 'supported', 'summary': 'Resistance-exercise EMG directly supports deltoid recruitment in lateral/front raise families; lateral raises emphasize shoulder musculature and front raises emphasize anterior deltoid.', 'references': ['shoulder_training_emg_2012', 'lateral_raise_emg_2020']}, 'shoulder_external_rotation': {'status': 'supported', 'summary': 'Intramuscular/surface EMG directly supports infraspinatus and teres-minor as principal external rotators, with deltoid/scapular muscles contributing by position.', 'references': ['external_rotation_emg_2004', 'external_rotation_roles_2012']}, 'elbow_flexion': {'status': 'supported', 'summary': 'Curl studies directly support biceps brachii as a prime elbow flexor across dumbbell, straight-bar and EZ-bar variants.', 'references': ['biceps_curl_emg_2013', 'curl_variants_emg_2018']}, 'elbow_flexion_brachioradialis_bias': {'status': 'supported', 'summary': 'Curl-variant EMG directly supports substantial brachioradialis involvement and grip-dependent changes in elbow-flexor recruitment.', 'references': ['curl_variants_emg_2018']}, 'elbow_extension': {'status': 'supported', 'summary': 'Direct EMG evidence supports long- and lateral-head triceps recruitment during loaded elbow-extension exercises.', 'references': ['triceps_extension_emg_2017']}, 'wrist_flexion': {'status': 'provisional', 'summary': 'Rule is biomechanically plausible but has not yet been assigned targeted pattern-level literature in DB++.', 'references': []}, 'wrist_extension': {'status': 'provisional', 'summary': 'Rule is biomechanically plausible but has not yet been assigned targeted pattern-level literature in DB++.', 'references': []}, 'squat': {'status': 'supported', 'summary': 'Systematic-review evidence supports high gluteus-maximus activation across squats, lunges, step-ups and related loaded lower-body movements; quadriceps dominance is also well established in squat-family work.', 'references': ['glute_strength_review_2020']}, 'squat_quad_bias': {'status': 'supported', 'summary': 'Systematic-review evidence supports high gluteus-maximus activation across squats, lunges, step-ups and related loaded lower-body movements; quadriceps dominance is also well established in squat-family work.', 'references': ['glute_strength_review_2020']}, 'lunge': {'status': 'supported', 'summary': 'Systematic-review evidence supports high gluteus-maximus activation across squats, lunges, step-ups and related loaded lower-body movements; quadriceps dominance is also well established in squat-family work.', 'references': ['glute_strength_review_2020']}, 'step_up': {'status': 'supported', 'summary': 'Systematic-review evidence supports high gluteus-maximus activation across squats, lunges, step-ups and related loaded lower-body movements; quadriceps dominance is also well established in squat-family work.', 'references': ['glute_strength_review_2020']}, 'knee_extension': {'status': 'supported', 'summary': 'Longitudinal resistance-training studies show knee-extension training produces quadriceps hypertrophy, directly supporting quadriceps as the target muscle group.', 'references': ['leg_extension_hypertrophy_2021', 'leg_extension_comparison_2026']}, 'knee_flexion': {'status': 'supported', 'summary': 'Direct EMG evidence supports hamstring activation across leg curl, GHR, good morning and RDL variants.', 'references': ['hamstring_exercises_2014']}, 'hip_hinge': {'status': 'supported', 'summary': 'Deadlift systematic review supports substantial quadriceps, erector-spinae, gluteal and hamstring activation, with variant-specific differences.', 'references': ['deadlift_systematic_review_2020']}, 'hip_extension': {'status': 'supported', 'summary': 'Hip-thrust and hamstring exercise literature supports strong gluteal/hamstring contribution with variant-specific erector-spinae involvement.', 'references': ['hip_thrust_systematic_review_2019', 'hamstring_exercises_2014']}, 'glute_ham_raise': {'status': 'supported', 'summary': 'Hip-thrust and hamstring exercise literature supports strong gluteal/hamstring contribution with variant-specific erector-spinae involvement.', 'references': ['hip_thrust_systematic_review_2019', 'hamstring_exercises_2014']}, 'rack_pull': {'status': 'supported', 'summary': 'Deadlift systematic review supports substantial quadriceps, erector-spinae, gluteal and hamstring activation, with variant-specific differences.', 'references': ['deadlift_systematic_review_2020']}, 'anti_rotation': {'status': 'indirect_support', 'summary': 'Pallof-press research directly establishes a laterally loaded lumbopelvic postural-control task; related trunk-stabilization literature supports abdominal recruitment, but exact direct/indirect set roles remain an extrapolation.', 'references': ['pallof_press_postural_2025', 'bridge_stabilization_emg_2012']}, 'hip_abduction': {'status': 'supported', 'summary': 'Systematic-review evidence supports gluteal activation in hip-abduction/external-rotation exercise families; adduction mapping remains primarily anatomical.', 'references': ['hip_abduction_review_2015']}, 'hip_adduction': {'status': 'supported', 'summary': 'Systematic-review evidence supports gluteal activation in hip-abduction/external-rotation exercise families; adduction mapping remains primarily anatomical.', 'references': ['hip_abduction_review_2015']}, 'plantar_flexion_straight_knee': {'status': 'supported', 'summary': 'Standing/knee-extended calf-raise training produces gastrocnemius and soleus hypertrophy; EMG studies confirm triceps-surae recruitment during plantar flexion.', 'references': ['calf_raise_hypertrophy_2023', 'calf_raise_emg_2021']}, 'leg_press': {'status': 'supported', 'summary': 'Systematic-review evidence supports high gluteus-maximus activation across squats, lunges, step-ups and related loaded lower-body movements; quadriceps dominance is also well established in squat-family work.', 'references': ['glute_strength_review_2020']}, 'conventional_deadlift': {'status': 'supported', 'summary': 'Deadlift systematic review supports substantial quadriceps, erector-spinae, gluteal and hamstring activation, with variant-specific differences.', 'references': ['deadlift_systematic_review_2020']}, 'sumo_deadlift': {'status': 'supported', 'summary': 'Deadlift systematic review supports substantial quadriceps, erector-spinae, gluteal and hamstring activation, with variant-specific differences.', 'references': ['deadlift_systematic_review_2020']}, 'chest_fly': {'status': 'supported', 'summary': 'Bench-press literature supports pectoralis major and triceps as major prime movers with anterior deltoid contribution; inclination changes relative contribution.', 'references': ['bench_systematic_review_2017', 'bench_inclination_2020']}, 'pullover': {'status': 'supported', 'summary': 'Direct barbell-pullover EMG demonstrates pectoralis-major and latissimus-dorsi recruitment, with pectoralis activation exceeding latissimus in the tested setup.', 'references': ['pullover_emg_2011']}, 'upright_row': {'status': 'supported', 'summary': 'Direct upright-row EMG demonstrates deltoid and trapezius recruitment, with grip width altering relative activation.', 'references': ['upright_row_grip_emg_2012']}, 'face_pull': {'status': 'indirect_support', 'summary': 'No exact face-pull study was located in this pass; the mapping is supported indirectly by closely related external-rotation, reverse-fly and upper-back/shoulder EMG evidence.', 'references': ['external_rotation_emg_2004', 'shoulder_training_emg_2012']}, 'shoulder_flexion': {'status': 'supported', 'summary': 'Resistance-exercise EMG directly supports deltoid recruitment in lateral/front raise families; lateral raises emphasize shoulder musculature and front raises emphasize anterior deltoid.', 'references': ['shoulder_training_emg_2012', 'lateral_raise_emg_2020']}, 'shoulder_internal_rotation': {'status': 'supported', 'summary': 'EMG directly supports subscapularis as a major internal rotator, with arm position strongly affecting selective activation.', 'references': ['internal_rotation_emg_2003', 'subscapularis_exercise_2003']}, 'hip_flexion': {'status': 'supported', 'summary': 'A systematic review and fine-wire EMG evidence directly support iliopsoas and related hip-flexor recruitment during leg raises and loaded hip-flexion tasks.', 'references': ['hip_flexor_systematic_review_2024', 'psoas_aslr_emg_2010']}, 'plantar_flexion_bent_knee': {'status': 'supported', 'summary': 'Seated/bent-knee calf raises directly load the triceps surae, with comparatively greater soleus emphasis than straight-leg calf raising.', 'references': ['calf_raise_hypertrophy_2023', 'calf_raise_swelling_2023', 'calf_raise_emg_2021']}, 'dorsiflexion': {'status': 'provisional', 'summary': 'Rule is biomechanically plausible but has not yet been assigned targeted pattern-level literature in DB++.', 'references': []}, 'anti_extension': {'status': 'supported', 'summary': 'Prone bridge/plank and rollout-style stabilization studies directly demonstrate substantial rectus-abdominis and oblique activation under anti-extension demands.', 'references': ['bridge_stabilization_emg_2012', 'bridge_surface_emg_2013']}, 'lateral_flexion': {'status': 'supported', 'summary': 'Side-bridge/lateral-trunk EMG studies directly demonstrate high internal/external oblique and abdominal recruitment.', 'references': ['side_bridge_oblique_emg_2020', 'side_bridge_asymmetry_2022']}, 'farmer_carry': {'status': 'complex_supported', 'summary': "Strongman EMG/biomechanics directly included the farmer's walk and documents substantial whole-body, hip and trunk loading; DB++ role labels summarize the event.", 'references': ['strongman_trunk_events_2009']}, 'loaded_carry': {'status': 'complex_supported', 'summary': 'Strongman EMG/biomechanics directly studied farmer, suitcase, keg and yoke-style carries and demonstrates large torso/hip stabilization demands.', 'references': ['strongman_trunk_events_2009']}, 'sled_push': {'status': 'supported', 'summary': 'Direct sled-push EMG shows lower-limb loading, with increasing resistance increasing vastus-lateralis and gastrocnemius activity.', 'references': ['sled_push_emg_2021']}, 'sled_pull': {'status': 'indirect_support', 'summary': 'Direct sled-push evidence supports resisted locomotor lower-limb loading, while strongman carry/drag biomechanics support the whole-body loading context; exact backward-pull muscle weighting remains extrapolated.', 'references': ['sled_push_emg_2021', 'strongman_trunk_events_2009']}, 'kettlebell_swing': {'status': 'complex_supported', 'summary': 'Kettlebell EMG/biomechanics literature supports whole-body ballistic loading with strong hip-extensor and trunk demands; exact set-credit roles remain model abstractions.', 'references': ['kettlebell_emg_2017', 'kettlebell_swing_2012']}, 'olympic_clean_pull': {'status': 'complex_supported', 'summary': 'Olympic-lift literature supports rapid coordinated hip/knee/ankle extension and substantial lower-body/trapezius involvement; DB++ direct/indirect labels remain whole-exercise bookkeeping abstractions across phases.', 'references': ['olympic_emg_2026', 'olympic_position_2023', 'olympic_kinetics_2012']}, 'olympic_clean': {'status': 'complex_supported', 'summary': 'Olympic-lift literature supports rapid coordinated hip/knee/ankle extension and substantial lower-body/trapezius involvement; DB++ direct/indirect labels remain whole-exercise bookkeeping abstractions across phases.', 'references': ['olympic_emg_2026', 'olympic_position_2023', 'olympic_kinetics_2012']}, 'olympic_snatch_pull': {'status': 'complex_supported', 'summary': 'Olympic-lift literature supports rapid coordinated hip/knee/ankle extension and substantial lower-body/trapezius involvement; DB++ direct/indirect labels remain whole-exercise bookkeeping abstractions across phases.', 'references': ['olympic_emg_2026', 'olympic_position_2023', 'olympic_kinetics_2012']}, 'olympic_snatch': {'status': 'complex_supported', 'summary': 'Olympic-lift literature supports rapid coordinated hip/knee/ankle extension and substantial lower-body/trapezius involvement; DB++ direct/indirect labels remain whole-exercise bookkeeping abstractions across phases.', 'references': ['olympic_emg_2026', 'olympic_position_2023', 'olympic_kinetics_2012']}, 'olympic_jerk': {'status': 'complex_supported', 'summary': 'Olympic-lift literature supports rapid coordinated hip/knee/ankle extension and substantial lower-body/trapezius involvement; DB++ direct/indirect labels remain whole-exercise bookkeeping abstractions across phases.', 'references': ['olympic_emg_2026', 'olympic_position_2023', 'olympic_kinetics_2012']}, 'olympic_clean_and_jerk': {'status': 'complex_supported', 'summary': 'Olympic-lift literature supports rapid coordinated hip/knee/ankle extension and substantial lower-body/trapezius involvement; DB++ direct/indirect labels remain whole-exercise bookkeeping abstractions across phases.', 'references': ['olympic_emg_2026', 'olympic_position_2023', 'olympic_kinetics_2012']}, 'snatch_balance': {'status': 'complex_supported', 'summary': 'Olympic-lift literature supports rapid coordinated hip/knee/ankle extension and substantial lower-body/trapezius involvement; DB++ direct/indirect labels remain whole-exercise bookkeeping abstractions across phases.', 'references': ['olympic_emg_2026', 'olympic_position_2023', 'olympic_kinetics_2012']}, 'push_press': {'status': 'complex_supported', 'summary': 'Olympic-lift literature supports rapid coordinated hip/knee/ankle extension and substantial lower-body/trapezius involvement; DB++ direct/indirect labels remain whole-exercise bookkeeping abstractions across phases.', 'references': ['olympic_emg_2026', 'olympic_position_2023', 'olympic_kinetics_2012']}, 'kettlebell_clean': {'status': 'complex_supported', 'summary': 'Kettlebell EMG/biomechanics literature supports whole-body ballistic loading with strong hip-extensor and trunk demands; exact set-credit roles remain model abstractions.', 'references': ['kettlebell_emg_2017', 'kettlebell_swing_2012']}, 'kettlebell_snatch': {'status': 'complex_supported', 'summary': 'Kettlebell EMG/biomechanics literature supports whole-body ballistic loading with strong hip-extensor and trunk demands; exact set-credit roles remain model abstractions.', 'references': ['kettlebell_emg_2017', 'kettlebell_swing_2012']}, 'kettlebell_jerk': {'status': 'complex_supported', 'summary': 'Kettlebell EMG/biomechanics literature supports whole-body ballistic loading with strong hip-extensor and trunk demands; exact set-credit roles remain model abstractions.', 'references': ['kettlebell_emg_2017', 'kettlebell_swing_2012']}, 'kettlebell_windmill': {'status': 'complex_supported', 'summary': 'Kettlebell EMG/biomechanics literature supports whole-body ballistic loading with strong hip-extensor and trunk demands; exact set-credit roles remain model abstractions.', 'references': ['kettlebell_emg_2017', 'kettlebell_swing_2012']}, 'kettlebell_sumo_high_pull': {'status': 'complex_supported', 'summary': 'Kettlebell EMG/biomechanics literature supports whole-body ballistic loading with strong hip-extensor and trunk demands; exact set-credit roles remain model abstractions.', 'references': ['kettlebell_emg_2017', 'kettlebell_swing_2012']}, 'thruster': {'status': 'complex_supported', 'summary': 'Kettlebell EMG/biomechanics literature supports whole-body ballistic loading with strong hip-extensor and trunk demands; exact set-credit roles remain model abstractions.', 'references': ['kettlebell_emg_2017', 'kettlebell_swing_2012']}, 'muscle_up': {'status': 'indirect_support', 'summary': 'Pull-up EMG literature directly supports latissimus, biceps, posterior deltoid/mid-trapezius involvement; row/climb/muscle-up roles partly extrapolate from related pulling mechanics.', 'references': ['pullup_emg_2017']}, 'rope_climb': {'status': 'indirect_support', 'summary': 'Pull-up EMG literature directly supports latissimus, biceps, posterior deltoid/mid-trapezius involvement; row/climb/muscle-up roles partly extrapolate from related pulling mechanics.', 'references': ['pullup_emg_2017']}, 'atlas_stone_load': {'status': 'complex_supported', 'summary': 'Strongman literature supports multi-phase whole-body loading. Pattern roles summarize the event rather than representing a single-joint stimulus.', 'references': ['atlas_stone_2021', 'tire_flip_2010', 'strongman_trunk_2009', 'strongman_review_2019']}, 'loaded_object_load': {'status': 'complex_supported', 'summary': 'Strongman literature supports multi-phase whole-body loading. Pattern roles summarize the event rather than representing a single-joint stimulus.', 'references': ['atlas_stone_2021', 'tire_flip_2010', 'strongman_trunk_2009', 'strongman_review_2019']}, 'tire_flip': {'status': 'complex_supported', 'summary': 'Strongman literature supports multi-phase whole-body loading. Pattern roles summarize the event rather than representing a single-joint stimulus.', 'references': ['atlas_stone_2021', 'tire_flip_2010', 'strongman_trunk_2009', 'strongman_review_2019']}, 'strongman_overhead': {'status': 'complex_supported', 'summary': 'Strongman literature supports multi-phase whole-body loading. Pattern roles summarize the event rather than representing a single-joint stimulus.', 'references': ['atlas_stone_2021', 'tire_flip_2010', 'strongman_trunk_2009', 'strongman_review_2019']}, 'strongman_carry': {'status': 'complex_supported', 'summary': 'Strongman literature supports multi-phase whole-body loading. Pattern roles summarize the event rather than representing a single-joint stimulus.', 'references': ['atlas_stone_2021', 'tire_flip_2010', 'strongman_trunk_2009', 'strongman_review_2019']}, 'power_stairs': {'status': 'complex_supported', 'summary': 'Strongman literature supports multi-phase whole-body loading. Pattern roles summarize the event rather than representing a single-joint stimulus.', 'references': ['atlas_stone_2021', 'tire_flip_2010', 'strongman_trunk_2009', 'strongman_review_2019']}, 'battle_ropes': {'status': 'supported', 'summary': 'Direct battle-rope EMG demonstrates moderate-to-high anterior-deltoid, oblique and lumbar-extensor activation, with additional studies confirming whole-body recruitment.', 'references': ['battle_rope_emg_2015', 'battle_rope_wbv_emg_2015']}, 'bent_press': {'status': 'indirect_support', 'summary': 'No targeted peer-reviewed bent-press EMG study was located; DB++ retains indirect support from strongman whole-body/trunk loading and lateral-trunk evidence.', 'references': ['strongman_trunk_events_2009', 'side_bridge_oblique_emg_2020']}, 'kettlebell_figure8': {'status': 'complex_supported', 'summary': 'Kettlebell EMG/biomechanics literature supports whole-body ballistic loading with strong hip-extensor and trunk demands; exact set-credit roles remain model abstractions.', 'references': ['kettlebell_emg_2017', 'kettlebell_swing_2012']}, 'kettlebell_pirate_ships': {'status': 'complex_supported', 'summary': 'Kettlebell EMG/biomechanics literature supports whole-body ballistic loading with strong hip-extensor and trunk demands; exact set-credit roles remain model abstractions.', 'references': ['kettlebell_emg_2017', 'kettlebell_swing_2012']}, 'drag_with_press': {'status': 'complex_supported', 'summary': 'Strongman literature supports multi-phase whole-body loading. Pattern roles summarize the event rather than representing a single-joint stimulus.', 'references': ['atlas_stone_2021', 'tire_flip_2010', 'strongman_trunk_2009', 'strongman_review_2019']}, 'spider_crawl': {'status': 'indirect_support', 'summary': 'No exact spider-crawl EMG study was located in this pass; quadruped/plank stabilization evidence supports trunk involvement while upper-body roles remain movement-mechanics extrapolations.', 'references': ['bridge_stabilization_emg_2012', 'bridge_surface_emg_2013']}, 'medicine_ball_slam': {'status': 'indirect_support', 'summary': 'No exact medicine-ball-slam muscle-role trial was located in this pass; the mapping is supported indirectly by ballistic whole-body/trunk and shoulder activation evidence.', 'references': ['battle_rope_emg_2015', 'bridge_stabilization_emg_2012']}, 'trunk_flexion': {'status': 'supported', 'summary': 'Loaded crunch and sit/curl-up EMG studies directly support rectus abdominis and oblique recruitment during trunk-flexion exercise.', 'references': ['crunch_loaded_emg_2009', 'situp_curlup_emg_2008']}, 'trunk_extension': {'status': 'supported', 'summary': 'Roman-chair and machine back-extension EMG directly supports erector-spinae loading with meaningful gluteal and hamstring contribution depending on technique.', 'references': ['back_extension_roman_chair_2014', 'back_extension_comparison_2021']}, 'trunk_rotation': {'status': 'supported', 'summary': 'Rotational training increases internal/external oblique thickness, and flexion-rotation EMG directly demonstrates rectus-abdominis and internal-oblique loading.', 'references': ['trunk_rotation_rct_2021', 'flexion_rotation_emg_2020']}, 'neck_flexion': {'status': 'supported', 'summary': 'Isometric cervical EMG studies directly support neck-flexor recruitment during resisted flexion.', 'references': ['neck_isometric_emg_2002', 'neck_conditioning_emg_2008']}, 'neck_extension': {'status': 'supported', 'summary': 'Isometric cervical EMG studies directly support posterior neck-muscle recruitment during resisted extension.', 'references': ['neck_isometric_emg_2002', 'neck_conditioning_emg_2008']}, 'neck_lateral_flexion': {'status': 'supported', 'summary': 'Cervical EMG studies directly measure direction-specific neck-muscle recruitment during resisted lateral flexion.', 'references': ['neck_isometric_emg_2002']}, 'forearm_pronation': {'status': 'supported', 'summary': 'Direct EMG evidence supports pronator quadratus and pronator teres recruitment during resisted forearm pronation.', 'references': ['forearm_pronation_supination_emg_2026']}, 'forearm_supination': {'status': 'supported', 'summary': 'Direct EMG evidence supports supinator and load-dependent biceps recruitment during resisted forearm supination.', 'references': ['forearm_pronation_supination_emg_2026']}, 'grip': {'status': 'supported', 'summary': 'Direct handgrip EMG studies support substantial forearm flexor/extensor recruitment during loaded gripping and pinching tasks.', 'references': ['forearm_grip_emg_2019', 'power_grip_emg_2015']}}


LABEL_MAP = {
    "lower back": "lower_back",
    "middle back": "middle_back",
}

NON_VOLUME_CATEGORIES = {"stretching", "cardio", "plyometrics"}

PATTERNS: dict[str, dict[str, list[str]]] = {
    "horizontal_press": {
        "direct": ["chest"],
        "indirect": ["triceps", "shoulders"],
        "stabilizers": [],
    },
    "incline_press": {
        "direct": ["chest", "shoulders"],
        "indirect": ["triceps"],
        "stabilizers": [],
    },
    "decline_press": {
        "direct": ["chest"],
        "indirect": ["triceps", "shoulders"],
        "stabilizers": [],
    },
    "vertical_press": {
        "direct": ["shoulders"],
        "indirect": ["triceps"],
        "stabilizers": ["abdominals"],
    },
    "horizontal_press_triceps_bias": {
        "direct": ["triceps", "chest"],
        "indirect": ["shoulders"],
        "stabilizers": [],
    },
    "dip_chest_bias": {
        "direct": ["chest", "triceps"],
        "indirect": ["shoulders"],
        "stabilizers": [],
    },
    "dip_triceps_bias": {
        "direct": ["triceps", "chest"],
        "indirect": ["shoulders"],
        "stabilizers": [],
    },
    "horizontal_pull": {
        "direct": ["middle_back", "lats"],
        "indirect": ["biceps", "shoulders"],
        "stabilizers": ["forearms"],
    },
    "vertical_pull": {
        "direct": ["lats"],
        "indirect": ["biceps", "middle_back"],
        "stabilizers": ["forearms"],
    },
    "shrug": {
        "direct": ["traps"],
        "indirect": [],
        "stabilizers": ["forearms"],
    },
    "reverse_fly": {
        "direct": ["shoulders", "middle_back"],
        "indirect": ["traps"],
        "stabilizers": [],
    },
    "shoulder_abduction": {
        "direct": ["shoulders"],
        "indirect": ["traps"],
        "stabilizers": [],
    },
    "shoulder_external_rotation": {
        "direct": ["rotator_cuff"],
        "indirect": [],
        "stabilizers": [],
    },
    "elbow_flexion": {
        "direct": ["biceps"],
        "indirect": ["forearms"],
        "stabilizers": [],
    },
    "elbow_flexion_brachioradialis_bias": {
        "direct": ["biceps", "forearms"],
        "indirect": [],
        "stabilizers": [],
    },
    "elbow_extension": {
        "direct": ["triceps"],
        "indirect": [],
        "stabilizers": [],
    },
    "wrist_flexion": {
        "direct": ["forearms"], "indirect": [], "stabilizers": []
    },
    "wrist_extension": {
        "direct": ["forearms"], "indirect": [], "stabilizers": []
    },
    "squat": {
        "direct": ["quadriceps", "glutes"],
        "indirect": ["adductors"],
        "stabilizers": ["lower_back", "hamstrings", "calves"],
    },
    "squat_quad_bias": {
        "direct": ["quadriceps"],
        "indirect": ["glutes", "adductors"],
        "stabilizers": ["lower_back"],
    },
    "lunge": {
        "direct": ["quadriceps", "glutes"],
        "indirect": ["adductors"],
        "stabilizers": ["hamstrings", "calves"],
    },
    "step_up": {
        "direct": ["quadriceps", "glutes"],
        "indirect": ["adductors"],
        "stabilizers": ["calves"],
    },
    "knee_extension": {
        "direct": ["quadriceps"], "indirect": [], "stabilizers": []
    },
    "knee_flexion": {
        "direct": ["hamstrings"], "indirect": ["calves"], "stabilizers": []
    },
    "hip_hinge": {
        "direct": ["hamstrings", "glutes"],
        "indirect": [],
        "stabilizers": ["lower_back", "forearms"],
    },
    "hip_extension": {
        "direct": ["glutes"],
        "indirect": ["hamstrings"],
        "stabilizers": ["lower_back"],
    },
    "glute_ham_raise": {
        "direct": ["hamstrings", "glutes"],
        "indirect": ["calves"],
        "stabilizers": [],
    },
    "rack_pull": {
        "direct": ["glutes", "hamstrings"],
        "indirect": [],
        "stabilizers": ["lower_back", "traps", "forearms", "lats"],
    },
    "anti_rotation": {
        "direct": ["abdominals"],
        "indirect": [],
        "stabilizers": [],
    },
    "hip_abduction": {
        "direct": ["abductors"], "indirect": ["glutes"], "stabilizers": []
    },
    "hip_adduction": {
        "direct": ["adductors"], "indirect": [], "stabilizers": []
    },
    "plantar_flexion_straight_knee": {
        "direct": ["calves"], "indirect": [], "stabilizers": []
    },
    "leg_press": {
        "direct": ["quadriceps", "glutes"],
        "indirect": ["adductors"],
        "stabilizers": [],
    },
    "conventional_deadlift": {
        "direct": ["glutes", "hamstrings"],
        "indirect": ["quadriceps"],
        "stabilizers": ["lower_back", "traps", "forearms", "lats"],
    },
    "sumo_deadlift": {
        "direct": ["glutes", "quadriceps", "adductors"],
        "indirect": ["hamstrings"],
        "stabilizers": ["lower_back", "traps", "forearms"],
    },
    "chest_fly": {
        "direct": ["chest"], "indirect": [], "stabilizers": ["shoulders"]
    },
    "pullover": {
        "direct": ["lats"], "indirect": ["chest"], "stabilizers": ["triceps"]
    },
    "upright_row": {
        "direct": ["shoulders", "traps"],
        "indirect": ["biceps"],
        "stabilizers": ["forearms"],
    },
    "face_pull": {
        "direct": ["shoulders", "middle_back"],
        "indirect": ["traps", "biceps"],
        "stabilizers": ["forearms"],
    },
    "shoulder_flexion": {
        "direct": ["shoulders"], "indirect": [], "stabilizers": []
    },
    "shoulder_internal_rotation": {
        "direct": ["rotator_cuff"], "indirect": [], "stabilizers": []
    },
    "hip_flexion": {
        "direct": ["hip_flexors"], "indirect": ["abdominals"], "stabilizers": []
    },
    "plantar_flexion_bent_knee": {
        "direct": ["calves"], "indirect": [], "stabilizers": []
    },
    "dorsiflexion": {
        "direct": ["tibialis"], "indirect": [], "stabilizers": []
    },
    "anti_extension": {
        "direct": ["abdominals"], "indirect": [], "stabilizers": ["shoulders"]
    },
    "lateral_flexion": {
        "direct": ["abdominals"], "indirect": [], "stabilizers": []
    },
    "farmer_carry": {
        "direct": ["forearms", "traps"],
        "indirect": [],
        "stabilizers": ["abdominals", "lower_back"],
    },
    "loaded_carry": {
        "direct": ["forearms"], "indirect": ["traps"],
        "stabilizers": ["abdominals", "lower_back"],
    },
    "sled_push": {
        "direct": ["quadriceps", "glutes"], "indirect": ["calves"],
        "stabilizers": ["abdominals"],
    },
    "sled_pull": {
        "direct": ["quadriceps", "glutes"], "indirect": ["hamstrings", "calves"],
        "stabilizers": ["forearms"],
    },
    "kettlebell_swing": {
        "direct": ["glutes", "hamstrings"], "indirect": [],
        "stabilizers": ["lower_back", "forearms"],
    },
    "olympic_clean_pull": {
        "direct": ["quadriceps", "glutes", "traps"],
        "indirect": ["hamstrings", "calves"],
        "stabilizers": ["lower_back", "forearms", "abdominals"],
    },
    "olympic_clean": {
        "direct": ["quadriceps", "glutes", "traps"],
        "indirect": ["hamstrings", "calves"],
        "stabilizers": ["lower_back", "forearms", "abdominals", "shoulders"],
    },
    "olympic_snatch_pull": {
        "direct": ["quadriceps", "glutes", "traps"],
        "indirect": ["hamstrings", "calves"],
        "stabilizers": ["lower_back", "forearms", "abdominals"],
    },
    "olympic_snatch": {
        "direct": ["quadriceps", "glutes", "traps"],
        "indirect": ["hamstrings", "calves"],
        "stabilizers": ["shoulders", "triceps", "lower_back", "forearms", "abdominals"],
    },
    "olympic_jerk": {
        "direct": ["shoulders", "triceps", "quadriceps", "glutes"],
        "indirect": ["calves"],
        "stabilizers": ["abdominals", "traps"],
    },
    "olympic_clean_and_jerk": {
        "direct": ["quadriceps", "glutes", "traps", "shoulders", "triceps"],
        "indirect": ["hamstrings", "calves"],
        "stabilizers": ["lower_back", "forearms", "abdominals"],
    },
    "snatch_balance": {
        "direct": ["quadriceps", "glutes"],
        "indirect": ["shoulders", "triceps"],
        "stabilizers": ["traps", "abdominals"],
    },
    "push_press": {
        "direct": ["shoulders", "triceps", "quadriceps", "glutes"],
        "indirect": ["calves"],
        "stabilizers": ["abdominals", "traps"],
    },
    "kettlebell_clean": {
        "direct": ["glutes", "hamstrings"],
        "indirect": ["quadriceps", "traps"],
        "stabilizers": ["forearms", "lower_back", "abdominals"],
    },
    "kettlebell_snatch": {
        "direct": ["glutes", "hamstrings"],
        "indirect": ["quadriceps", "traps", "shoulders"],
        "stabilizers": ["forearms", "lower_back", "abdominals"],
    },
    "kettlebell_jerk": {
        "direct": ["shoulders", "triceps", "quadriceps", "glutes"],
        "indirect": ["calves"],
        "stabilizers": ["forearms", "abdominals", "traps"],
    },
    "kettlebell_windmill": {
        "direct": ["abdominals"],
        "indirect": ["glutes", "hamstrings"],
        "stabilizers": ["shoulders", "triceps"],
    },
    "kettlebell_sumo_high_pull": {
        "direct": ["glutes", "quadriceps", "traps", "shoulders"],
        "indirect": ["hamstrings", "adductors", "biceps"],
        "stabilizers": ["forearms", "abdominals"],
    },
    "thruster": {
        "direct": ["quadriceps", "glutes", "shoulders", "triceps"],
        "indirect": ["calves"],
        "stabilizers": ["abdominals", "traps"],
    },
    "muscle_up": {
        "direct": ["lats", "chest", "triceps"],
        "indirect": ["biceps", "shoulders", "middle_back"],
        "stabilizers": ["forearms", "abdominals"],
    },
    "rope_climb": {
        "direct": ["lats", "biceps", "forearms"],
        "indirect": ["middle_back"],
        "stabilizers": ["abdominals"],
    },
    "atlas_stone_load": {
        "direct": ["glutes", "quadriceps", "hamstrings"],
        "indirect": ["biceps", "traps"],
        "stabilizers": ["forearms", "lower_back", "abdominals"],
    },
    "loaded_object_load": {
        "direct": ["glutes", "quadriceps", "hamstrings"],
        "indirect": ["biceps", "traps"],
        "stabilizers": ["forearms", "lower_back", "abdominals"],
    },
    "tire_flip": {
        "direct": ["glutes", "quadriceps", "hamstrings"],
        "indirect": ["chest", "triceps", "calves"],
        "stabilizers": ["lower_back", "forearms", "abdominals"],
    },
    "strongman_overhead": {
        "direct": ["shoulders", "triceps", "quadriceps", "glutes"],
        "indirect": ["traps", "calves"],
        "stabilizers": ["forearms", "lower_back", "abdominals"],
    },
    "strongman_carry": {
        "direct": ["quadriceps", "glutes"],
        "indirect": ["traps", "biceps"],
        "stabilizers": ["abdominals", "lower_back"],
    },
    "power_stairs": {
        "direct": ["quadriceps", "glutes"],
        "indirect": ["hamstrings", "calves"],
        "stabilizers": ["lower_back", "abdominals"],
    },
    "battle_ropes": {
        "direct": ["shoulders"],
        "indirect": ["forearms", "chest"],
        "stabilizers": ["abdominals"],
    },
    "bent_press": {
        "direct": ["abdominals", "shoulders"],
        "indirect": ["glutes", "hamstrings", "triceps"],
        "stabilizers": ["lower_back", "quadriceps"],
    },
    "kettlebell_figure8": {
        "direct": ["abdominals"],
        "indirect": ["glutes", "hamstrings", "shoulders"],
        "stabilizers": ["forearms", "lower_back"],
    },
    "kettlebell_pirate_ships": {
        "direct": ["shoulders", "abdominals"],
        "indirect": ["lats"],
        "stabilizers": ["forearms", "lower_back"],
    },
    "drag_with_press": {
        "direct": ["quadriceps", "glutes", "chest", "triceps"],
        "indirect": ["calves", "hamstrings", "shoulders"],
        "stabilizers": ["abdominals", "forearms"],
    },
    "spider_crawl": {
        "direct": ["abdominals"],
        "indirect": ["shoulders", "chest", "triceps"],
        "stabilizers": ["glutes"],
    },
    "medicine_ball_slam": {
        "direct": ["abdominals", "lats"],
        "indirect": ["shoulders"],
        "stabilizers": ["glutes", "quadriceps"],
    },

    "trunk_flexion": {
        "direct": ["abdominals"], "indirect": [], "stabilizers": []
    },
    "trunk_extension": {
        "direct": ["lower_back"],
        "indirect": ["glutes", "hamstrings"],
        "stabilizers": [],
    },
    "trunk_rotation": {
        "direct": ["abdominals"], "indirect": [], "stabilizers": []
    },
    "forearm_pronation": {
        "direct": ["forearms"], "indirect": [], "stabilizers": []
    },
    "forearm_supination": {
        "direct": ["forearms"], "indirect": ["biceps"], "stabilizers": []
    },
    "grip": {
        "direct": ["forearms"], "indirect": [], "stabilizers": []
    },
    "neck_lateral_flexion": {
        "direct": ["neck"], "indirect": [], "stabilizers": []
    },
    "neck_flexion": {
        "direct": ["neck"], "indirect": [], "stabilizers": []
    },
    "neck_extension": {
        "direct": ["neck"], "indirect": [], "stabilizers": []
    },
}

# Exact overrides are the highest-precedence semantic layer.
# This initial list is intentionally small and should grow through review.
OVERRIDES: dict[str, dict[str, Any]] = {
    "Isometric_Neck_Exercise_-_Front_And_Back": {
        "patterns": ["neck_flexion", "neck_extension"],
        "direct": ["neck"],
        "indirect": [],
        "stabilizers": [],
        "confidence": "high",
        "reviewReasons": [],
    },
    "Barbell_Bench_Press_-_Medium_Grip": {
        "patterns": ["horizontal_press"],
        "direct": ["chest"],
        "indirect": ["triceps", "shoulders"],
        "stabilizers": [],
        "confidence": "high",
        "reviewReasons": [],
    },
    "Barbell_Full_Squat": {
        "patterns": ["squat"],
        "direct": ["quadriceps", "glutes"],
        "indirect": ["adductors"],
        "stabilizers": ["hamstrings", "lower_back", "calves"],
        "confidence": "high",
        "reviewReasons": [],
    },

    "Pullups": {
        "patterns": ["vertical_pull"],
        "direct": ["lats"],
        "indirect": ["biceps", "middle_back"],
        "stabilizers": ["forearms"],
        "confidence": "high",
        "reviewReasons": [],
    },
    "Dips_-_Chest_Version": {
        "patterns": ["dip_chest_bias"],
        "direct": ["chest", "triceps"],
        "indirect": ["shoulders"],
        "stabilizers": [],
        "confidence": "high",
        "reviewReasons": [],
    },
    "Dips_-_Triceps_Version": {
        "patterns": ["dip_triceps_bias"],
        "direct": ["triceps", "chest"],
        "indirect": ["shoulders"],
        "stabilizers": [],
        "confidence": "high",
        "reviewReasons": [],
    },
    "Glute_Ham_Raise": {
        "patterns": ["glute_ham_raise"],
        "direct": ["hamstrings", "glutes"],
        "indirect": ["calves"],
        "stabilizers": [],
        "confidence": "high",
        "reviewReasons": [],
    },
    "Natural_Glute_Ham_Raise": {
        "patterns": ["glute_ham_raise"],
        "direct": ["hamstrings", "glutes"],
        "indirect": ["calves"],
        "stabilizers": [],
        "confidence": "high",
        "reviewReasons": [],
    },

}

def normalize_muscle(label: str) -> str:
    return LABEL_MAP.get(label, label.replace(" ", "_"))

def normalized_list(labels: list[str]) -> list[str]:
    return dedupe([normalize_muscle(x) for x in labels])

def dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))

def infer_pattern(exercise: dict[str, Any]) -> str | None:
    name = exercise.get("name", "").lower()
    primary = set(exercise.get("primaryMuscles", []))

    # Highly specific rules before generic ones.
    # v0.4.1: resolve the remaining known named movements.
    if name == "alternating hang clean":
        return "olympic_clean"
    if name == "dumbbell clean":
        return "olympic_clean"
    if name == "bottoms-up clean from the hang position":
        return "kettlebell_clean"
    if name == "anti-gravity press":
        return "vertical_press"
    if name == "bent press":
        return "bent_press"
    if name == "forward drag with press":
        return "drag_with_press"
    if name in {"kettlebell figure 8", "kettlebell pass between the legs"}:
        return "kettlebell_figure8"
    if name == "kettlebell pirate ships":
        return "kettlebell_pirate_ships"
    if name == "landmine 180's":
        return "trunk_rotation"
    if name == "one-arm kettlebell para press":
        return "vertical_press"
    if name == "one-arm medicine ball slam":
        return "medicine_ball_slam"
    if name == "spider crawl":
        return "spider_crawl"

    # v0.4: Olympic weightlifting and related derivatives.
    if name == "clean and jerk":
        return "olympic_clean_and_jerk"
    if name in {"clean pull"}:
        return "olympic_clean_pull"
    if name in {"snatch pull"}:
        return "olympic_snatch_pull"
    if "snatch balance" in name:
        return "snatch_balance"
    if name in {"clean", "power clean", "hang clean", "split clean", "clean from blocks",
                "power clean from blocks", "hang clean - below the knees",
                "smith machine hang power clean"}:
        return "olympic_clean"
    if name in {"snatch", "power snatch", "hang snatch", "split snatch", "muscle snatch",
                "snatch from blocks", "power snatch from blocks", "hang snatch - below knees"}:
        return "olympic_snatch"
    if name in {"jerk balance", "power jerk", "split jerk"}:
        return "olympic_jerk"
    if name == "clean and press":
        return "olympic_clean_and_jerk"

    # Kettlebell ballistic families.
    if "kettlebell" in name and "clean and jerk" in name:
        return "olympic_clean_and_jerk"
    if "kettlebell" in name and "push press" in name:
        return "push_press"
    if "kettlebell" in name and ("jerk" in name):
        return "kettlebell_jerk"
    if "kettlebell" in name and "snatch" in name:
        return "kettlebell_snatch"
    if "kettlebell" in name and ("clean" in name):
        return "kettlebell_clean"
    if "kettlebell" in name and "windmill" in name:
        return "kettlebell_windmill"
    if "kettlebell" in name and "sumo high pull" in name:
        return "kettlebell_sumo_high_pull"
    if "kettlebell" in name and "thruster" in name:
        return "thruster"

    # Strongman / loaded-object families.
    if "atlas stone" in name:
        return "atlas_stone_load"
    if any(x in name for x in ["keg load", "sandbag load"]):
        return "loaded_object_load"
    if "tire flip" in name:
        return "tire_flip"
    if any(x in name for x in ["log lift", "circus bell", "rack delivery"]):
        return "strongman_overhead"
    if "conan" in name and "wheel" in name:
        return "strongman_carry"
    if "power stairs" in name:
        return "power_stairs"

    # Gymnastic / climbing / integrated.
    if "muscle up" in name:
        return "muscle_up"
    if "rope climb" in name:
        return "rope_climb"
    if "battling ropes" in name:
        return "battle_ropes"

    # v0.3.2 exact conventional-name cleanup.
    if name == "machine shoulder (military) press":
        return "vertical_press"
    if name in {"hip extension with bands", "hip lift with band", "physioball hip bridge"}:
        return "hip_extension"
    if name == "cuban press":
        return "shoulder_external_rotation"
    if name in {"air bike", "bottoms up", "otis-up"}:
        return "trunk_flexion"
    if name in {"plate twist", "standing cable lift", "cable judo flip"}:
        return "trunk_rotation"
    if name == "flutter kicks":
        return "hip_flexion"
    if name == "dumbbell raise":
        return "shoulder_flexion"
    if name == "barbell incline shoulder raise":
        return "shoulder_flexion"
    if name == "neck press":
        return "horizontal_press"
    if name in {"push press", "push press - behind the neck"}:
        return "push_press"
    if name in {"landmine linear jammer", "single-arm linear jammer"}:
        return "push_press"
    if "incline" in name and ("press" in name or "push-up" in name or "push up" in name or "bench" in name):
        return "incline_press"
    if "decline" in name and ("press" in name or "push-up" in name or "push up" in name):
        return "decline_press"
    if any(x in name for x in ["floor press", "board press", "pin press", "chain press"]):
        return "horizontal_press_triceps_bias"
    if any(x in name for x in ["close-grip dumbbell press", "close grip dumbbell press",
                               "close-grip ez-bar press", "close grip ez-bar press",
                               "jm press"]):
        return "horizontal_press_triceps_bias"
    if ("bench press" in name or "chest press" in name or "push-up" in name or "push up" in name
            or "pushups" in name or "floor press" in name):
        return "horizontal_press"
    if ("military press" in name or "overhead press" in name or "shoulder press" in name
            or "arnold press" in name or "arnold dumbbell press" in name
            or "seated dumbbell press" in name or "standing dumbbell press" in name
            or "kettlebell press" in name or "bradford" in name
            or "machine shoulder military press" in name
            or "standing alternating dumbbell press" in name
            or "kettlebell seated press" in name or "kettlebell seesaw press" in name
            or "see-saw press" in name or "seesaw press" in name
            or "press behind neck" in name or "press behind the neck" in name
            or "palms-in dumbbell press" in name or "palm-in one-arm dumbbell press" in name):
        return "vertical_press"
    if any(x in name for x in ["dips - chest version", "parallel bar dip", "ring dips"]):
        return "dip_chest_bias"
    if any(x in name for x in ["dips - triceps version", "bench dips", "bench dip",
                               "weighted bench dip", "dip machine"]):
        return "dip_triceps_bias"
    if ("pull-up" in name or "pull up" in name or "pullup" in name or "pullups" in name
            or "chin-up" in name or "chin up" in name or "chins" in name
            or "mixed grip chin" in name or "pulldown" in name or "v-bar pullup" in name):
        return "vertical_pull"
    # v0.7.4 remaining deterministic fallback cleanup.
    if name in {
        "power partials", "standing low-pulley deltoid raise",
        "alternating deltoid raise"
    }:
        return "shoulder_abduction"
    if name in {
        "single dumbbell raise", "standing dumbbell straight-arm front delt raise above head",
        "standing front barbell raise over head", "smith incline shoulder raise"
    }:
        return "shoulder_flexion"
    if name == "reverse machine flyes":
        return "reverse_fly"
    if name in {"one-legged cable kickback", "leg lift"}:
        return "hip_extension"
    if name == "dumbbell lying pronation":
        return "forearm_pronation"
    if name == "dumbbell lying supination":
        return "forearm_supination"
    if name in {
        "plate pinch", "standing olympic plate hand squeeze",
        "wrist roller", "wrist rotations with straight bar"
    }:
        return "grip"
    if name in {"lying face down plate neck resistance", "seated head harness neck resistance"}:
        return "neck_extension"
    if name == "lying face up plate neck resistance":
        return "neck_flexion"
    if name == "isometric neck exercise - sides":
        return "neck_lateral_flexion"

    # v0.7.3 deterministic isolation cleanup: exact/unambiguous names only.
    if name in {
        "bodyweight flyes", "flat bench cable flyes", "incline cable flye",
        "cable iron cross"
    }:
        return "chest_fly"
    if name in {
        "front cable raise", "front dumbbell raise", "front incline dumbbell raise",
        "front plate raise", "front two-dumbbell raise", "dumbbell incline shoulder raise"
    }:
        return "shoulder_flexion"
    if name in {"band pull apart", "band pull-apart"}:
        return "reverse_fly"
    if name == "dumbbell scaption":
        return "shoulder_abduction"
    if name in {"butt lift (bridge)", "butt lift bridge"}:
        return "hip_extension"

    if "face pull" in name:
        return "face_pull"
    if "upright row" in name:
        return "upright_row"
    if "row" in name:
        return "horizontal_pull"
    if "shrug" in name:
        return "shrug"
    if "pullover" in name or "pull-over" in name:
        return "pullover"
    if "svend press" in name:
        return "horizontal_press"
    if any(x in name for x in ["pec deck", "butterfly", "chest fly", "chest flye",
                               "dumbbell fly", "dumbbell flye", "cable crossover",
                               "cross over - with bands", "around the worlds"]):
        return "chest_fly"
    if "reverse fly" in name or "back fly" in name or "rear delt" in name:
        return "reverse_fly"
    if "lateral raise" in name or "side lateral" in name:
        return "shoulder_abduction"
    if "front raise" in name:
        return "shoulder_flexion"
    if "external rotation" in name:
        return "shoulder_external_rotation"
    if "internal rotation" in name:
        return "shoulder_internal_rotation"
    if "hammer curl" in name or "reverse curl" in name:
        return "elbow_flexion_brachioradialis_bias"
    if "curl" in name and ("leg curl" not in name):
        return "elbow_flexion"
    if any(x in name for x in ["triceps extension", "tricep extension", "pushdown", "pressdown", "skull crusher"]):
        return "elbow_extension"
    if "reverse wrist curl" in name or "wrist extension" in name:
        return "wrist_extension"
    if "wrist curl" in name:
        return "wrist_flexion"
    if "leg press" in name:
        return "leg_press"
    if "leg extension" in name:
        return "knee_extension"
    if "leg curl" in name:
        return "knee_flexion"
    if "step-up" in name or "step up" in name:
        return "step_up"
    if any(x in name for x in ["lunge", "split squat"]):
        return "lunge"
    if "front squat" in name or "hack squat" in name:
        return "squat_quad_bias"
    if "squat" in name:
        return "squat"
    if "rack pull" in name:
        return "rack_pull"
    if "sumo deadlift" in name:
        return "sumo_deadlift"
    if any(x in name for x in ["romanian deadlift", "stiff-legged deadlift", "stiff legged deadlift",
                               "stiff-leg deadlift", "wide stance stiff legs", "good morning"]):
        return "hip_hinge"
    if "deadlift" in name:
        return "conventional_deadlift"
    if any(x in name for x in ["hip thrust", "glute bridge", "glute kickback",
                                 "glute kick back", "pull-through", "pull through"]):
        return "hip_extension"
    if any(x in name for x in ["hip flexion", "knee raise", "leg raise"]):
        return "hip_flexion"
    if "monster walk" in name:
        return "hip_abduction"
    if "abduction" in name:
        return "hip_abduction"
    if "adduction" in name:
        return "hip_adduction"
    if "seated calf" in name or "seated toe raise" in name:
        return "plantar_flexion_bent_knee"
    if "calf raise" in name or "calf press" in name or "toe raise" in name:
        return "plantar_flexion_straight_knee"
    if "tibialis raise" in name or "dorsiflexion" in name:
        return "dorsiflexion"
    if any(x in name for x in ["ab wheel", "ab roller", "rollout", "roll-out"]):
        return "anti_extension"
    if "side bend" in name or "side plank" in name:
        return "lateral_flexion"
    if "pallof press" in name:
        return "anti_rotation"
    if any(x in name for x in ["side bridge", "side jackknife"]):
        return "lateral_flexion"
    if any(x in name for x in ["dead bug", "butt-ups", "cocoons", "elbow to knee",
                               "leg pull-in", "leg pull in", "hanging pike",
                               "bent-knee hip raise", "bent knee hip raise",
                               "exercise ball pull-in", "exercise ball pull in"]):
        return "trunk_flexion"
    if any(x in name for x in ["crunch", "sit-up", "sit up"]):
        return "trunk_flexion"
    if "plank" in name:
        return "anti_extension"
    if "back extension" in name or "hyperextension" in name:
        return "trunk_extension"
    if ("russian twist" in name or "wood chop" in name or "woodchop" in name
            or "torso rotation" in name or "plate twist" in name
            or "standing cable lift" in name or "london bridges" in name):
        return "trunk_rotation"
    if "farmer" in name and "walk" in name:
        return "farmer_carry"
    if exercise.get("category") == "strongman" and ("carry" in name or "walk" in name):
        return "loaded_carry"
    if "sled push" in name or "prowler" in name:
        return "sled_push"
    if "backward drag" in name:
        return "sled_pull"
    if "sled" in name and ("pull" in name or "drag" in name):
        return "sled_pull"
    if "kettlebell swing" in name:
        return "kettlebell_swing"

    # A small muscle-informed assist for obvious isolation records.
    if exercise.get("mechanic") == "isolation":
        if primary == {"quadriceps"}:
            return "knee_extension"
        if primary == {"hamstrings"}:
            return "knee_flexion"
        if primary == {"biceps"}:
            return "elbow_flexion"
        if primary == {"triceps"}:
            return "elbow_extension"
        if primary == {"calves"}:
            return "plantar_flexion_straight_knee"
        if primary == {"abdominals"}:
            return "trunk_flexion"
        if primary == {"adductors"}:
            return "hip_adduction"
        if primary == {"abductors"}:
            return "hip_abduction"

    # Other named integrated movements kept medium-confidence rather than fallback-low.
    if name in {"iron cross", "isometric wipers"}:
        return "anti_extension"
    if name in {"landmine 180s", "spell caster"}:
        return "trunk_rotation"
    if name == "sled overhead backward walk":
        return "sled_pull"

    return None

def roles_from_pattern(pattern: str) -> tuple[list[str], list[str], list[str]]:
    rule = PATTERNS[pattern]
    return (
        list(rule["direct"]),
        list(rule["indirect"]),
        list(rule["stabilizers"]),
    )

def remove_role_overlap(direct: list[str], indirect: list[str], stabilizers: list[str]):
    direct = dedupe(direct)
    indirect = [x for x in dedupe(indirect) if x not in direct]
    stabilizers = [
        x for x in dedupe(stabilizers)
        if x not in direct and x not in indirect
    ]
    return direct, indirect, stabilizers


def classify_exercise(exercise: dict[str, Any]) -> dict[str, list[str]]:
    category = (exercise.get("category") or "").lower()
    equipment = (exercise.get("equipment") or "").lower()
    name = (exercise.get("name") or "").lower().strip()

    training = []
    category_map = {
        "strength": "strength",
        "powerlifting": "powerlifting",
        "olympic weightlifting": "olympic_weightlifting",
        "strongman": "strongman",
        "plyometrics": "plyometrics",
        "cardio": "cardio",
        "stretching": "stretching",
    }
    if category in category_map:
        training.append(category_map[category])
    if category in {"powerlifting", "olympic weightlifting", "strongman"}:
        training.insert(0, "strength")

    modalities = []
    equipment_map = {
        "body only": "bodyweight",
        "barbell": "free_weight",
        "dumbbell": "free_weight",
        "e-z curl bar": "free_weight",
        "machine": "machine",
        "cable": "cable",
        "bands": "band",
        "kettlebells": "kettlebell",
        "medicine ball": "medicine_ball",
        "foam roll": "foam_roll",
    }
    if equipment in equipment_map:
        modalities.append(equipment_map[equipment])
    elif equipment:
        modalities.append("other")
    if "kettlebell" in name:
        modalities.append("kettlebell")
    if "sled" in name or "prowler" in name or "drag" in name:
        modalities.append("sled")
    if "rope" in name:
        modalities.append("rope")
    if category == "strongman" and any(x in name for x in ["stone", "keg", "log", "tire", "sandbag", "yoke", "conan"]):
        modalities.append("loaded_object")
    if not modalities:
        modalities = ["other"]

    contexts = ["general_fitness"]
    if category == "powerlifting":
        contexts.append("powerlifting")
    if category == "olympic weightlifting":
        contexts.append("weightlifting")
    if category == "strongman":
        contexts.append("strongman")
    if any(x in name for x in ["kipping muscle up", "muscle up", "thruster", "wall ball", "double under", "toes to bar"]):
        contexts.append("crossfit")
    if any(x in name for x in ["muscle up", "ring dip", "iron cross"]):
        contexts.append("gymnastics")

    competition = []
    if category == "powerlifting":
        if name in {"squat", "barbell full squat"}:
            competition.append("powerlifting_squat")
        if "bench press" in name and all(x not in name for x in ["incline", "decline", "close-grip", "close grip"]):
            competition.append("powerlifting_bench_press")
        if name in {"deadlift", "barbell deadlift"}:
            competition.append("powerlifting_deadlift")
    if category == "olympic weightlifting":
        if name == "snatch":
            competition.append("weightlifting_snatch")
        if name == "clean and jerk":
            competition.append("weightlifting_clean_and_jerk")

    return {
        "trainingTypes": dedupe(training),
        "modalities": dedupe(modalities),
        "sportContexts": dedupe(contexts),
        "competitionMovements": dedupe(competition),
    }


def evidence_refs_for_annotation(annotation: dict[str, Any]) -> list[str]:
    return [f"pattern:{p}" for p in annotation.get("patterns", [])]

def annotate(exercise: dict[str, Any]) -> dict[str, Any]:
    category = exercise.get("category")
    name = (exercise.get("name") or "").lower().strip()

    # Some upstream "strength" records are not resistance-set exercises for DB++.
    if name in {"wind sprints", "balance board"}:
        return {
            "patterns": [],
            "direct": [],
            "indirect": [],
            "stabilizers": [],
            "volumeEligible": False,
            "confidence": "high",
            "reviewReasons": ["non_volume_named_override"],
        }
    eligible = category not in NON_VOLUME_CATEGORIES

    if not eligible:
        return {
            "patterns": [],
            "direct": [],
            "indirect": [],
            "stabilizers": [],
            "volumeEligible": False,
            "confidence": "high",
            "reviewReasons": [f"non_volume_category:{category}"],
        }

    exercise_id = exercise["id"]
    if exercise_id in OVERRIDES:
        ann = copy.deepcopy(OVERRIDES[exercise_id])
        ann["volumeEligible"] = True
        return ann

    pattern = infer_pattern(exercise)
    if pattern is not None:
        direct, indirect, stabilizers = roles_from_pattern(pattern)
        direct, indirect, stabilizers = remove_role_overlap(direct, indirect, stabilizers)
        complex_patterns = {
            "olympic_clean_pull", "olympic_clean", "olympic_snatch_pull", "olympic_snatch",
            "olympic_jerk", "olympic_clean_and_jerk", "snatch_balance", "push_press",
            "kettlebell_clean", "kettlebell_snatch", "kettlebell_jerk", "kettlebell_windmill",
            "kettlebell_sumo_high_pull", "thruster", "muscle_up", "rope_climb",
            "atlas_stone_load", "loaded_object_load", "tire_flip", "strongman_overhead",
            "strongman_carry", "power_stairs", "battle_ropes", "bent_press",
            "kettlebell_figure8", "kettlebell_pirate_ships", "drag_with_press",
            "spider_crawl", "medicine_ball_slam"
        }
        evidence_status = PATTERN_EVIDENCE.get(pattern, {}).get("status", "provisional")

        # v0.7 evidence-driven confidence policy.
        if evidence_status == "supported":
            confidence = "high"
            reasons = []
        elif evidence_status == "complex_supported":
            confidence = "medium"
            reasons = ["complex_pattern_bookkeeping"]
        elif evidence_status == "indirect_support":
            confidence = "medium"
            reasons = ["indirect_evidence_pattern"]
        else:
            confidence = "medium"
            reasons = ["provisional_pattern_evidence"]
        return {
            "patterns": [pattern],
            "direct": direct,
            "indirect": indirect,
            "stabilizers": stabilizers,
            "volumeEligible": True,
            "confidence": confidence,
            "reviewReasons": reasons,
        }

    primary = normalized_list(exercise.get("primaryMuscles", []))
    secondary = normalized_list(exercise.get("secondaryMuscles", []))
    direct, indirect, stabilizers = remove_role_overlap(primary, secondary, [])

    if exercise.get("mechanic") == "isolation":
        confidence = "medium"
        reasons = ["isolation_primary_secondary_fallback"]
    else:
        confidence = "low"
        reasons = ["compound_fallback_requires_review"]

    # If the upstream includes a muscle outside our current ontology, preserve
    # source data but omit that label from annotations and flag it.
    unknown = [m for m in direct + indirect if m not in MUSCLES]
    if unknown:
        direct = [m for m in direct if m in MUSCLES]
        indirect = [m for m in indirect if m in MUSCLES]
        reasons.append("unknown_upstream_muscle:" + ",".join(sorted(set(unknown))))
        confidence = "low"

    return {
        "patterns": [],
        "direct": direct,
        "indirect": indirect,
        "stabilizers": stabilizers,
        "volumeEligible": True,
        "confidence": confidence,
        "reviewReasons": reasons,
    }

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def convert(source_path: Path, completeness: str) -> dict[str, Any]:
    with source_path.open("r", encoding="utf-8") as f:
        source = json.load(f)

    if not isinstance(source, list):
        raise ValueError("Expected upstream combined JSON to be an array of exercise objects")

    exercises: dict[str, Any] = {}
    for item in source:
        exercise_id = item["id"]
        annotation = annotate(item)
        annotation["evidenceRefs"] = evidence_refs_for_annotation(annotation)
        exercises[exercise_id] = {
            "exerciseId": exercise_id,
            "classification": classify_exercise(item),
            "annotation": annotation,
            "source": item,
        }

    return {
        "metadata": {
            "schemaVersion": SCHEMA_VERSION,
            "converterVersion": CONVERTER_VERSION,
            "generatedAt": (
                dt.datetime.fromtimestamp(
                    int(os.environ["SOURCE_DATE_EPOCH"]),
                    tz=dt.timezone.utc,
                ).isoformat()
                if os.environ.get("SOURCE_DATE_EPOCH")
                else dt.datetime.now(dt.timezone.utc).isoformat()
            ),
            "upstream": {
                "project": "yuhonas/free-exercise-db",
                "sourceUrl": UPSTREAM_URL,
                "sha256": sha256_file(source_path),
            },
            "setCredits": SET_CREDITS,
            "setCreditEvidence": {
                "status": "supported_model",
                "interpretation": "Direct sets count as 1.0, indirect sets as 0.5, and stabilizer-only involvement as 0.0. This is the single DB++ set-credit model.",
                "references": ["fractional_sets_meta_regression_2025"],
            },
            "evidence": {
                "references": EVIDENCE_REFERENCES,
                "patterns": PATTERN_EVIDENCE,
            },
            "muscleOntology": MUSCLES,
            "sourceExerciseCount": len(source),
            "outputExerciseCount": len(exercises),
            "completeness": completeness,
        },
        "exercises": exercises,
    }

def validate(data: dict[str, Any], schema_path: Path) -> None:
    try:
        import jsonschema
    except ImportError as e:
        raise SystemExit(
            "Schema validation requested but jsonschema is not installed. "
            "Run: python3 -m pip install jsonschema"
        ) from e

    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(data)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Upstream combined exercises.json")
    parser.add_argument("output", type=Path, help="Output FEDB++ JSON")
    parser.add_argument("--schema", type=Path, help="Optional DB++ JSON Schema to validate output")
    parser.add_argument(
        "--completeness",
        choices=["full", "fixture", "partial"],
        default="full",
        help="Provenance marker written to output metadata",
    )
    args = parser.parse_args()

    data = convert(args.source, args.completeness)

    if args.schema:
        validate(data, args.schema)

    with args.output.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(
        f"Wrote {len(data['exercises'])} exercises to {args.output} "
        f"(completeness={args.completeness})"
    )

if __name__ == "__main__":
    main()
