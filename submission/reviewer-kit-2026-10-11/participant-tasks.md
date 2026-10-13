# Lumen: tasks for an independent reviewer

Please work from the interface, tell the moderator when each task is finished, and give your final answer in your own words. You may stop at any time. You do not need to supply personal health information. This session is about a public-data research interface; it is not a medical assessment.

You receive one task at a time. The moderator can repeat a task exactly but cannot show you a solution. Please do not open the moderator guide, answer key, judging script, source code, or previous reviewers' answers during the session.

## T1 — Find an arbitrary record

Find **UCI411-276** in the complete cohort audit. For **LAD**, report its full-input probability, cutoff, recorded label, and whether the flag matches that label. State which record set you are searching. Finish with the record open in the explorer.

## T2 — Find an error shared by five profiles

Using the training-selected rule, find a **recorded positive LCX record missed by all five profiles**. Report the matching roster size and the selected record's ID. For that record, report the recorded outcome and the five profile flags. Also report the cohort count of errors among records with five agreeing flags. What can you conclude from the agreement?

## T3 — Change a decision rule

The moderator opens **UCI411-057**, full inputs, **LCX**, using the training-selected rule. Record its probability, cutoff and flag. Switch to the fixed 50% rule and report those three values again. Check the audit's missed-positive and false-alarm counts before and after. Explain what changed in the system and what you can infer from it.

## T4 — Compare available inputs

The moderator opens **UCI411-128**, **LAD**, using the training-selected rule. Compare all five input profiles, then select **History + examination**, and finally **All measurements**. Report each profile's flag, the two selected profiles' probabilities and cutoffs, and whether the explorer and explanation follow the selected cell. Explain what the differences between the profiles establish.

## T5 — Edit a record and examine its outcome comparison

The moderator opens **UCI411-128**, full inputs, with the original recorded labels revealed. Change only **Age from 62 to 63** and update the prediction. Try to compare the edited prediction with a recorded outcome and inspect the same-record profile comparison. Describe what the interface permits and why. Restore the recorded values, then show that the original comparison can be used again. Explain what the edit tells you.

## T6 — Trace anatomy to the complete score

The moderator opens **UCI411-171**, full inputs, starting with overall CAD selected. Select **LAD using its anatomy label or vessel mesh**. Rotate and zoom the view, focus or isolate that vessel, and restore the overview. Open the complete score calculation. Report the baseline, sum of all contributions, final score and LAD probability. Explain what the probability, vessel color, and a displayed contribution describe, and what the display can tell you about this person's anatomy.
