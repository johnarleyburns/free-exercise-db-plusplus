# Coaching policies

`CoachingPolicy` is a versioned Python model. The reference
`general-adaptive-v1` has explicit window, progression, adherence, volume,
frequency, substitution, regeneration, precedence, and parameter fields; it is
not a portable JSON schema.

Decision precedence is: hard constraints; structural invalidity; target
minimums; adherence; repeated failure; progression; target optimization;
preferences; continuity; stable lexical tie-breaking. The current reference
implementation supports canonical progression, repeated-performance load
regression, conservative effective-set edits, and generator-backed structural
regeneration. Unsupported or ambiguous evidence is reported as a hold or
insufficient-data decision rather than guessed at.
