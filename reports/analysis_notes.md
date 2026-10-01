# Validation notes

The current clean model is a dispatch-safe CatBoost classifier with chronological validation.

The target rate after order-level deduplication is about 11.4%, so a naive all-negative classifier is already close to 88.6% accuracy. For this reason, ROC-AUC and average precision are treated as primary ranking metrics.

Leakage diagnostic: adding `last_service_event_type` and pickup-presence information produces near-perfect validation performance, which is exactly why those fields are excluded from the real model.
