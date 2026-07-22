# Question Record Schema

One JSON object per line (JSONL). Fields:

| Field | Type | Notes |
|---|---|---|
| `id` | string | `<domain>-<number>`, e.g. `hl7-003`. Stable once assigned. |
| `domain` | string | `hl7v2` \| `dicom` \| `fhir` |
| `type` | string | `factual` \| `false_premise` \| `version_trap` \| `deprecated` |
| `question` | string | Exactly what is sent to the model. Self-contained; names the standard version where it matters. |
| `ground_truth` | string | The correct answer, stated plainly. For `false_premise`: what the correct challenge looks like. |
| `premise_note` | string | `false_premise` only — why the premise is false, for the grader. |
| `acceptable_answers` | array | Optional short forms the grader should also accept (e.g. `"PID-7"`, `"PID.7"`). |
| `difficulty` | string | `basic` \| `intermediate` \| `expert` (author-assigned) |
| `source` | string | Primary-source citation used for verification (standard + section). |
| `verification` | object | `{"status": "draft"\|"verified", "verified_by": "practitioner"\|null, "date": "YYYY-MM-DD"\|null}` |

Rules:

- A question is sent to models and counted in headline results only when `verification.status` is `"verified"`.
- Never edit `question` text after any model has been run against it — retire the id and issue a new one.
- No PHI, no vendor-proprietary information. Public standards only.
