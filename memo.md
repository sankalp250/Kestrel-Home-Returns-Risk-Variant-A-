# Kestrel Home - Returns Risk Pilot

**To:** Ritu Deshpande, Head of D2C Operations  
**Subject:** Pre-dispatch returns risk pilot

## Decision

Use the model as a **pre-dispatch prioritisation tool**, not an automatic cancellation rule. Score each order before release and route higher-risk orders to a confirmation/review step.

## The number

On a chronological future-period holdout starting **2 April 2026**, the dispatch-safe model achieved **0.7795 ROC-AUC** and **0.4053 average precision**. Accuracy at a 0.50 threshold was **89.24%**. Accuracy is not the primary measure because only about 11.5% of validation orders returned.

A separate model using service/pickup fields looked almost perfect (about **0.998 ROC-AUC**) but was rejected because those fields can be written after the return process starts.

## The rupees

Kestrel's policy puts the all-in return cost at **Rs 1,150** and a completed confirmation call at **Rs 45**. The spring pilot reportedly prevented about **35%** of returns on called orders.

**Break-even call risk = Rs 45 / (0.35 × Rs 1,150) ~  11.2%.**

Use **~12% as the working confirmation/review threshold**. Do not automate holds yet: the pack gives a 12% cancellation rate for holds longer than 24 hours, but not the financial value of those cancellations.

## Next week

1. Score dispatches before release.
2. Send the higher-risk group to confirmation/review; do not auto-cancel.
3. Track actual returns, intervention success, cancellations after holds, and Shield-customer outcomes.
4. Recalculate the threshold once Kestrel has observed intervention results and contribution-margin data.
