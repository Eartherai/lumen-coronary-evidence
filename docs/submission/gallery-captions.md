# Gallery order and captions

All five JPGs are unedited actual browser screenshots at 1440 x 960 (3:2), each under 5 MB. They show the final 13 October browser export. The development examples are public dataset records selected using known outcomes; they are not a human usability study or a new blinded clinical test.

1. **01-lumen-case-explorer.jpg**
   Caption: Four coronary predictions linked to named reference anatomy, measurements and exact feature contributions.
   Alt text: Lumen's case explorer shows a generic 3D heart and the LAD prediction for development record UCI411-171, with inputs and model contributions beside it.

2. **02-shared-missed-positive.jpg**
   Caption: A model mistake you can investigate: UCI411-020 has a positive recorded LCX label, despite a 22.2% estimate below its 33.0% research cutoff.
   Alt text: Selected LCX reference artery with a 22.2% prediction and its source-feature contributions for a recorded development missed-positive example.

3. **03-five-input-profiles.jpg**
   Caption: One record, five separately fitted input profiles. All five LCX flags miss this recorded positive; profile agreement is not confidence.
   Alt text: Five-profile comparison for UCI411-020, showing all four targets and each model's probability and training-selected cutoff.

4. **04-complete-error-audit.jpg**
   Caption: Inspect the complete development cohort. LCX profiles agree on 172 records and are wrong on 60; every record can be opened and traced.
   Alt text: The development audit is filtered to nine LCX missed positives shared by all five profiles, with UCI411-020 selected and cohort error counts visible.

5. **05-model-evidence.jpg**
   Caption: The separate 61-record frozen evaluation retains all four targets, classification metrics, false-positive/negative counts and limitations.
   Alt text: Lumen's held-out evaluation table shows CAD, LAD, LCX and RCA metrics, thresholds and errors, followed by the small-test and clinical-validity limitations.
