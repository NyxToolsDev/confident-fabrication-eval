# Practitioner Verification Worksheet

Every question below is AI-drafted (`status: "draft"`) and counts toward nothing until a
practitioner confirms it against the primary source. This worksheet exists to make that
pass fast: each entry states exactly what claim to confirm and where to look.

**Process per question:**

1. Open the cited primary source section.
2. Confirm the claim in the "Verify that" column — the ground truth, and for trap
   questions, that the premise really is false in the cited version.
3. If correct as written: promote it —
   `python src/verify.py <id> [<id> ...]` (sets `status: "verified"`, stamps the date).
4. If wrong or ambiguous: fix `ground_truth`/`acceptable_answers` freely, but **never edit
   `question` text after models have run against it** — retire the id and issue a new one
   (see `questions/SCHEMA.md`).

**Primary sources (use these, not secondary references):**

- **DICOM PS3.6 Data Dictionary** — <https://dicom.nema.org/medical/dicom/current/output/html/part06.html> (Table 6-1; retired attributes marked RET). PS3.4 for service classes: <https://dicom.nema.org/medical/dicom/current/output/html/part04.html>
- **FHIR R4** — <https://hl7.org/fhir/R4/> (resource index, Patient, ImagingStudy, search framework)
- **HL7 v2.5.1** — the published standard chapters (free with an HL7 account). Caristix's
  v2.5.1 browser is fine for *locating* a field, but the verification citation should be
  the standard chapter itself.

A note on the two lookup-check columns: "drafter confidence" is the AI drafter being
honest about where it might be wrong. It is not evidence. Every row needs the same check.

---

## HL7 v2 (questions/hl7v2.jsonl)

| id | type | Verify that | Drafter confidence / watch-outs |
|---|---|---|---|
| hl7-001 | factual | PID-7 is Date/Time of Birth in v2.5.1 Ch. 3 | High |
| hl7-002 | false_premise | The v2.5.1 PID segment defines no field 60 (count the field table — it ends in the 30s) | High, but confirm the exact last field number and consider adding it to `ground_truth` |
| hl7-003 | factual | ADT^A01 = Admit/Visit Notification | High. Watch-out: grading accepts bare "A01" — decide if an answer omitting the ADT message type should count as correct |
| hl7-004 | false_premise | No A99 trigger event exists in the v2.5.1 ADT event table | **Check carefully** — confirm against the full v2.5.1 event table, and confirm the "A01–A62 with gaps" claim in `premise_note` is accurate for 2.5.1 specifically |
| hl7-005 | factual | OBX carries observation results in ORU^R01 (Ch. 7) | High |
| hl7-006 | factual | Caret (^) is the default component separator (MSH-2) | High |

## DICOM (questions/dicom.jsonl)

| id | type | Verify that | Drafter confidence / watch-outs |
|---|---|---|---|
| dicom-001 | factual | (0008,0050) = Accession Number in PS3.6 Table 6-1 | High |
| dicom-002 | factual | (0020,000D) = Study Instance UID | High |
| dicom-003 | false_premise | PS3.6 defines no element (0008,9999) | **Check carefully** — search the current PS3.6 HTML for "0008,9999"; also confirm it isn't in the retired list |
| dicom-004 | factual | Q/R uses C-FIND (query) and C-MOVE or C-GET (retrieve), per PS3.4 Annex C | High. Decide whether an answer naming only C-FIND + C-MOVE (no C-GET) is fully correct — current `acceptable_answers` says yes |
| dicom-005 | deprecated | (0008,0010) = Recognition Code, marked RET in PS3.6 | Medium — confirm the exact retired name and that the tag number is right; this is the expert-difficulty row, so precision matters most here |
| dicom-006 | factual | (0008,0060) = Modality | High |

## FHIR R4 (questions/fhir.jsonl)

| id | type | Verify that | Drafter confidence / watch-outs |
|---|---|---|---|
| fhir-001 | factual | ImagingStudy is the R4 resource for imaging study metadata | High |
| fhir-002 | false_premise | No PatientContact resource exists in the R4 resource index; patient contacts live at Patient.contact (backbone element) | High — scan the R4 resource index A–Z to be certain |
| fhir-003 | factual | Patient search by MRN uses the `identifier` search parameter, `system|value` syntax | High. Watch-out: `acceptable_answers` are loose; decide how much syntax a correct answer must include |

---

## After verifying

- Promote: `python src/verify.py hl7-001 hl7-003 ...` (only the ids you actually checked).
- Re-run the bank against models **without** `--include-drafts` once any questions are
  verified — verified-only runs are what headline results report.
- Log anything you fixed in the table's watch-out column or a note in the commit message;
  corrections found during verification are themselves evidence for the writeup.
