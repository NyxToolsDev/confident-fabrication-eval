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

## Batch 2 (drafted 2026-07-29, ids hl7-007–011, dicom-007–010, fhir-004–009)

### HL7 v2

| id | type | Verify that | Drafter confidence / watch-outs |
|---|---|---|---|
| hl7-007 | factual | PID-18 is Patient Account Number in v2.5.1 | High |
| hl7-008 | factual | MSH-9 components are Message Code ^ Trigger Event ^ Message Structure (MSG data type) | High |
| hl7-009 | factual | MSA-1 carries the ack code; AA/AE/AR are the original-mode values | High. Watch-out: enhanced mode adds CA/CE/CR — a model listing those too is still correct; consider noting that in `acceptable_answers` |
| hl7-010 | version_trap | PID ends at PID-30 in v2.3.1, and PID-32 (Identity Reliability Code) arrived in v2.4 | **Check carefully** — both halves of the claim need the 2.3.1 chapter and the 2.4 change history |
| hl7-011 | false_premise | The v2.5.1 standard defines no ZPD segment; Z-segments are site-defined by convention | High |

### DICOM

| id | type | Verify that | Drafter confidence / watch-outs |
|---|---|---|---|
| dicom-007 | factual | (0008,0018) = SOP Instance UID | High |
| dicom-008 | factual | C-ECHO / Verification SOP Class, UID 1.2.840.10008.1.1 | High — confirm the UID digit-for-digit |
| dicom-009 | factual | (0010,0020) = Patient ID | High |
| dicom-010 | false_premise | PS3.7 defines no C-UPDATE; DIMSE-C set is C-ECHO/C-STORE/C-FIND/C-GET/C-MOVE | High |

### FHIR R4

| id | type | Verify that | Drafter confidence / watch-outs |
|---|---|---|---|
| fhir-004 | factual | Observation is the R4 resource for individual results/measurements | High |
| fhir-005 | factual | ServiceRequest is the R4 resource for imaging/lab orders | High |
| fhir-006 | version_trap | DiagnosticOrder is absent from R4; lineage DSTU2 DiagnosticOrder → STU3 ProcedureRequest → R4 ServiceRequest | Medium — **confirm the lineage**, it's stated in `ground_truth` and must be exactly right |
| fhir-007 | factual | PUT [base]/Patient/[id] is the update interaction | High |
| fhir-008 | false_premise | Patient has no mrn element; MRN lives in Patient.identifier | High |
| fhir-009 | factual | Coding is the datatype pairing code + system + display; CodeableConcept wraps Codings | High — check the question can't be fairly read as asking for CodeableConcept |

---

## Batch 3 (drafted 2026-07-29, ids hl7-012–018, dicom-011–017, fhir-010–015)

Trap-weighted on purpose: version traps ran at a 50% fabrication rate in the first
verified results, so this batch doubles down where the signal is.

### HL7 v2

| id | type | Verify that | Drafter confidence / watch-outs |
|---|---|---|---|
| hl7-012 | factual | OBR-4 is Universal Service Identifier in v2.5.1 Ch. 4 | High |
| hl7-013 | factual | PV1-2 is Patient Class, values from Table 0004 | High |
| hl7-014 | false_premise | The v2.5.1 MSH attribute table ends at MSH-21 (Message Profile Identifier); no MSH-25 | High on nonexistence — **confirm MSH-21 is the last field in 2.5.1 specifically** |
| hl7-015 | version_trap | v2.2 MSH-9 is two components only (message type ^ trigger event); MSG.3 arrived later | Medium — needs the actual v2.2 chapter; confirm which version introduced the third component before trusting `ground_truth`'s framing |
| hl7-016 | deprecated | PID-2 is backward-compatibility-only in v2.5.1; PID-3 is the replacement | High on the guidance — confirm the exact status wording ("B") in the 2.5.1 PID table |
| hl7-017 | factual | OBX-5 = Observation Value, OBX-2 = Value Type (Ch. 7) | High |
| hl7-018 | version_trap | v2.3.1 MSH ends at MSH-19; MSH-21 arrived in v2.4 as Conformance Statement ID (renamed Message Profile Identifier in 2.5) | **Check carefully** — both halves: the 2.3.1 MSH table AND the v2.4 name; the rename claim in `ground_truth` must match the standards |

### DICOM

| id | type | Verify that | Drafter confidence / watch-outs |
|---|---|---|---|
| dicom-011 | factual | (0010,0030) = Patient's Birth Date | High |
| dicom-012 | factual | 1.2.840.10008.1.2 = Implicit VR LE; 1.2.840.10008.1.2.1 = Explicit VR LE | High — digit-for-digit |
| dicom-013 | deprecated | Explicit VR Big Endian (1.2.840.10008.1.2.2) is retired in current DICOM | High on retired status — confirm how PS3.5/PS3.6 currently label it |
| dicom-014 | false_premise | No UID-checksum attribute exists; UI VR has no checksum mechanism | High |
| dicom-015 | factual | Modality Worklist FIND SOP Class = 1.2.840.10008.5.1.4.31 | **Check carefully** — digit-for-digit against PS3.6 Annex A / PS3.4 Annex K |
| dicom-016 | false_premise | PS3.7 DIMSE-N set is N-EVENT-REPORT/N-GET/N-SET/N-ACTION/N-CREATE/N-DELETE; no N-QUERY | High |
| dicom-017 | factual | (0020,000E) = Series Instance UID | High |

### FHIR R4

| id | type | Verify that | Drafter confidence / watch-outs |
|---|---|---|---|
| fhir-010 | factual | DiagnosticReport groups results; DiagnosticReport.result references Observations | High |
| fhir-011 | version_trap | MedicationOrder absent from R4; DSTU2 name, renamed MedicationRequest at STU3 | High — scan the R4 resource index |
| fhir-012 | version_trap | Conformance absent from R4; DSTU2 name, renamed CapabilityStatement at STU3 | High — same index scan |
| fhir-013 | factual | Date-range search uses the date parameter with ge/le (gt/lt) prefixes | High — decide how much syntax a correct answer must show |
| fhir-014 | false_premise | Observation has no resultStatus; status (1..1, observation-status value set) is the real element | High — also confirm the status cardinality/binding stated in `ground_truth` |
| fhir-015 | factual | _include adds referenced resources to the bundle; Observation:patient is a valid example | High — confirm the search-parameter name syntax in the R4 Search page |

---

## After verifying

- Promote: `python src/verify.py hl7-001 hl7-003 ...` (only the ids you actually checked).
- Re-run the bank against models **without** `--include-drafts` once any questions are
  verified — verified-only runs are what headline results report.
- Log anything you fixed in the table's watch-out column or a note in the commit message;
  corrections found during verification are themselves evidence for the writeup.
