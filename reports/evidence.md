# Kestrel Returns Risk - Evidence

## Dataset checks
- Raw training rows: 11155
- Duplicate order rows removed: 651
- Canonical training rows: 10504
- Validation rows: 2101
- Validation return rate: 11.52%
- Test predictions: 2096 rows; unique order IDs: 2096

## Model evidence
- roc_auc: 0.7795
- average_precision: 0.4053
- log_loss: 0.2975
- accuracy_at_0_5: 0.8924
- precision_at_0_5: 0.7667
- recall_at_0_5: 0.0950
- Best iteration: 223
- Validation start: 2026-04-02 00:23:00

## Leakage decision
- Excluded: last_service_event_type
- Excluded: pickup_scheduled_at
- Reason: these fields can be populated after the return process begins and therefore are not valid dispatch-time signals.

## Submission checks
- Columns: order_id, score
- Rows: 2096
- Score range: 0.016965 to 0.885261
- Null scores: 0
- Duplicate order IDs: 0

## Operational threshold check
- Working confirmation/review threshold: 0.12
- Validation orders flagged at 0.12: 632 / 2101
- Precision at 0.12: 0.2500
- Recall at 0.12: 0.6529
- At 0.50, the model makes few positive predictions; this confirms that the continuous score is more useful for ranking than a hard 50% classifier threshold.

## Failure mode
- The dominant 0.50-threshold error is false negatives: 219 returned orders were below 0.50 in the future-period holdout.
- Seven non-returned orders were above 0.50.
