# Specialized muscle coverage review — 2026-11-16

This change adds 11 original exercise records (938 total; 873 preserved upstream and 65 DB++ additions). No upstream ID, instruction, or source name is removed or rewritten. New records have original instructions and no copied images. Equipment demonstrations establish movement identity only; their marketing claims are not adopted.

## Added movements

| Group | Exercise ID | Name | Sources |
|---|---|---|---|
| tibialis | `Standing_Toe_Raise` | Standing Toe Raise | `nhs_toe_raise`, `nhs_strength_balance_toe_raise` |
| tibialis | `Band_Ankle_Dorsiflexion` | Band-Resisted Ankle Dorsiflexion | `aaos_ankle_conditioning` |
| tibialis | `Seated_Tib_Bar_Raise` | Seated Tib-Bar Raise | `tib_bar_manufacturer` |
| tibialis | `Single-Leg_Tib_Bar_Raise` | Single-Leg Tib-Bar Raise | `tib_bar_manufacturer` |
| hip_flexors | `Seated_Hip_Flexion` | Seated Hip Flexion | `osu_iliopsoas_progression`, `uw_seated_hip_flexion` |
| hip_flexors | `Supine_Short-Lever_Hip_Flexion` | Supine Short-Lever Hip Flexion | `osu_iliopsoas_progression` |
| hip_flexors | `Standing_Hip_Flexion_Hold` | Standing Hip-Flexion Hold | `cuh_hip_flexion` |
| neck | `Resisted_Neck_Rotation_Isometric` | Resisted Neck Rotation Isometric | `nhs_resisted_neck_rotation` |
| rotator_cuff | `Band_External_Rotation_90_Abduction` | Band External Rotation at 90 Degrees Abduction | `aaos_rotator_cuff_conditioning` |
| rotator_cuff | `Side-Lying_Dumbbell_Internal_Rotation` | Side-Lying Dumbbell Internal Rotation | `aaos_rotator_cuff_conditioning` |
| rotator_cuff | `Supine_Dumbbell_Shoulder_Rotation` | Supine Dumbbell Shoulder Rotation | `aaos_rotator_cuff_conditioning` |

All new movements earn direct 1.0 credit per eligible working set for the named group. Static holds retain their duration-based execution; catalog eligibility does not make a casual rehabilitation repetition a hard working set. No clinical program dosage is imported into the coaching engine. New movements have provisional preferred names in all 14 supported non-English locales, with locale → base language → English fallback.

## Duplicate resolution

- `External_Rotation` remains the canonical upstream ID and source record. Its English preferred display name becomes **Side-Lying Dumbbell External Rotation**; the old name and descriptive variants remain searchable aliases. No second record is added.
- `Hip_Flexion_with_Band` retains its ID and source record. **Standing Banded Hip Flexion**, **Banded March**, and **Resistance Band March** resolve to that record.
- The three new shoulder-rotation movements use distinct positions/load directions. They join the same descriptive shoulder-rotation family as the existing internal/external rotations. Family membership does not imply equal stimulus or substitution advice.
- Bilateral and unilateral tib-bar raises remain distinct equipment/laterality variants; their family is `tibialis_raise`.

## Partial-credit decisions

The existing accounting convention is direct **1.0**, indirect **0.5**, stabilizer **0.0**. EMG is evidence of involvement, not a measured conversion to hypertrophy sets. All new indirect-credit decisions are exact-ID, medium-confidence overrides with `indirect_evidence_pattern`; broad inference rules are unchanged.

| Decision | Scope | Reason |
|---|---|---|
| Add hip-flexor 0.5 | `Sit-Up`, `3_4_Sit-Up`, `Weighted_Sit-Ups_-_With_Bands` | Full torso elevation includes hip flexion. Fine-wire iliacus/psoas studies support involvement. Transfer to variants and the half-set convention remain model assumptions. |
| Add rotator-cuff 0.5 | `Dumbbell_Scaption` | Full-can scapular-plane elevation recruits supraspinatus; recorded as indirect contribution alongside deltoid/trapezius roles. |
| Add rotator-cuff 0.5, with uncertainty | `Reverse_Flyes_With_External_Rotation` | Prone full-can horizontal-abduction evidence supports cuff recruitment. Our incline version is not identical, and forearm rotation must not be mistaken for isolated shoulder rotation; retain medium confidence rather than extending this to ordinary flyes. |
| Keep tibialis partial credit at zero | Squat/lunge families | The reviewed split-squat study concerns held-posture ankle stability, not a demonstrated resistance-set hypertrophy contribution. No blanket half-set award. |
| Keep neck partial credit at zero | Shrug/carry families | A narrow-grip shrug protocol showed neck-strength transfer, but this does not establish independent neck hypertrophy volume for all shrug variants or justify double-counting trapezius work. |
| Keep other records unchanged | Curl-ups/crunches, Janda Sit-Up, Press Sit-Up, jackknife variants | Do not infer a new role from a name alone. Janda technique differs and its source makes an unverified inhibition claim; complex press/jackknife variants need separate review. Non-volume records remain ineligible. |

## References and reasons

Reference IDs below are embedded in `metadata.evidence.references` with the same `reason` text. Sources used for positive decisions are reachable through the exercise's `annotation.evidenceRefs` and pattern reference list. Negative findings are retained in the registry as audit evidence.

- **`aaos_ankle_conditioning`** — [Foot and Ankle Conditioning Program](https://www.orthoinfo.org/recovery/foot-and-ankle-conditioning-program/). **Reason:** Documents band-resisted dorsiflexion and identifies anterior tibialis; supports exercise selection, not a measured set-credit fraction.
- **`nhs_toe_raise`** — [Strength and balance exercise programme for falls prevention](https://www.southtees.nhs.uk/resources/strength-and-balance-exercise-programme-for-falls-prevention/). **Reason:** Documents lifting the forefoot while retaining heel contact; supports the bodyweight toe-raise movement.
- **`nhs_seated_toe_raise`** — [Lower limb strengthening activities](https://www.kentcht.nhs.uk/leaflet/lower-limb-strengthening-activities/). **Reason:** Documents seated toe lifts with heels down; supports toe-raise terminology and accessible progression.
- **`nhs_strength_balance_toe_raise`** — [Strength and balance exercises](https://www.nhsinform.scot/healthy-living/preventing-falls/keeping-well/strength-and-balance-exercises). **Reason:** Documents toe raises; corroborates bodyweight dorsiflexion as a distinct exercise from calf raises.
- **`tib_bar_manufacturer`** — [Tib Bar – Tibialis Trainer](https://tib-bar.com/products/tib-bar). **Reason:** Documents bilateral and unilateral tib-bar equipment and seated dorsiflexion technique only; commercial injury-prevention claims are not adopted.
- **`osu_iliopsoas_progression`** — [Gluteus Medius Repair: Appendix A, Psoas Progression](https://medicine.osu.edu/-/media/files/medicine/departments/sports-medicine/medical-professionals/hip/glute-med-repair-2020.pdf?hash=61FBA1E505B6173CD4D4C753FC8E8A8484725F81&la=en). **Reason:** Documents supine short-lever, seated, and standing resisted hip flexion; supports distinct positions, not transfer of postoperative dosage to general training.
- **`cuh_hip_flexion`** — [Hip strengthening exercises](https://www.cuh.nhs.uk/patient-information/hip-strengthening-exercises/). **Reason:** Documents supported standing hip flexion with the knee bent and a hold; supports the standing hip-flexion hold.
- **`uw_seated_hip_flexion`** — [Physical Therapy Before and After Your ACL Surgery: Seated Hip Flexion](https://healthonline.washington.edu/sites/default/files/record_pdfs/Physical-Therapy-Before-After-Your-ACL-Surgery-CH.pdf). **Reason:** Documents seated bent-knee hip flexion as distinct from a straight-leg raise; supports exercise identity only.
- **`nhs_resisted_neck_rotation`** — [Neck pain: Resisted neck exercises](https://www.dynamichealth.nhs.uk/help-and-advice/neck-pain/). **Reason:** Documents hand-resisted cervical rotation, flexion and side flexion; rotation is a distinct addition, while existing flexion/side records retain their IDs.
- **`aaos_rotator_cuff_conditioning`** — [Rotator Cuff and Shoulder Conditioning Program](https://www.orthoinfo.org/bodypart/shoulder/rotator-cuff-and-shoulder-conditioning-program/?webid=24DCE756). **Reason:** Documents 90-degree-abducted external rotation, supine rotation and side-lying internal/external rotation. Existing side-lying external rotation is retained with aliases.
- **`andersson_hip_flexor_emg_1997`** — [Abdominal and hip flexor muscle activation during various training exercises](https://pubmed.ncbi.nlm.nih.gov/9118976/). **Reason:** Fine-wire iliacus evidence supports hip-flexor involvement during hip-flexion sit-ups and leg lifts, without extending the claim to every curl-up.
- **`juker_psoas_emg_1998`** — [Quantitative intramuscular myoelectric activity of lumbar portions of psoas and the abdominal wall during a wide variety of tasks](https://pubmed.ncbi.nlm.nih.gov/9502361/). **Reason:** Sit-ups recruited psoas more than curl-ups. Supports exact full-sit-up indirect hip-flexor roles, not a measured 0.5 hypertrophy equivalence or general lifting credit.
- **`reinold_supraspinatus_emg_2007`** — [Electromyographic analysis of the supraspinatus and deltoid muscles during 3 common rehabilitation exercises](https://pubmed.ncbi.nlm.nih.gov/18174934/). **Reason:** Fine-wire EMG supports supraspinatus involvement in full-can scaption and prone horizontal abduction with external rotation. The incline reverse-fly mapping is a medium-confidence extrapolation; 0.5 remains the DB++ accounting convention.
- **`kim_split_squat_ankle_emg_2017`** — [Comparison of Activities of Tibialis Anterior, Peroneus Longus, and Tibialis Posterior Muscles according to Lunge Squats and Bulgarian Split Squats in a Healthy Population](https://www.jkema.org/archive/view_article?pid=jkema-1-1-26). **Reason:** Measures ankle-stability activation during held squat postures; insufficient to assign 0.5 tibialis sets to ordinary squats or lunges.
- **`neck_shrug_training_1997`** — [Effects of neck muscle training and detraining on neck muscle strength](https://www.jstage.jst.go.jp/article/jspfsm1949/46/2/46_2_201/_article/-char/en). **Reason:** Narrow-grip shrug intervention suggests neck-strength transfer in a specific protocol; does not establish an independent neck hypertrophy dose for all shrug variants, so no blanket 0.5 credit is awarded.

The clinical references describe movements and are not medical treatment prescriptions. This review changes catalog definitions and accounting annotations, not the published set-credit model.
