# Kestrel Home — Submission Form Draft

> This is a copy-ready draft for the online submission form. The original client files remain in `data/` and `client_pack/`. No `submission-form.md` is part of the project.

## Github Repo URL

`https://github.com/sankalp250/Kestrel-Home-Returns-Risk-Variant-A-`

The repository should be private because the supplied Kestrel data is client data and the policy prohibits public publication.

## What did you build, and what business decision does it support? State the number and the rupees.

Built a pre-dispatch return-risk service for Kestrel Home. It joins customer/product reference data to historical orders, scores each order with a dispatch-safe CatBoost model, returns a risk score plus employee-readable reasons through FastAPI, and provides a small operations screen for checking one order before dispatch.

On a chronological future-period validation set, the model achieved **0.7795 ROC-AUC** and **0.4053 average precision**. Accuracy at a 0.50 classification threshold was **89.24%**, but accuracy is not the primary metric because only about 11.5% of the validation orders returned.

The policy states that a return costs **₹1,150** and a completed pre-dispatch confirmation call costs **₹45**. With the pilot's reported 35% return-prevention rate, the rough break-even return probability for a call is **₹45 / (0.35 × ₹1,150) ≈ 11.2%**. The service therefore uses about **12% as the working confirmation threshold** and keeps the hold/cancellation decision separate until the financial cost of holding is known.

## What score do you expect predictions.csv to get on the hidden outcomes, on which metric, and why that metric? Say how you estimated it.

I expect the strongest comparable hidden-outcome metric to be **ROC-AUC**, because `predictions.csv` contains a continuous risk score and the evaluator can measure whether returned orders are ranked above non-returned orders.

My estimate is **roughly 0.77–0.80 ROC-AUC**, based on a chronological holdout covering future orders after **2026-04-02**, where the model achieved **0.7795 ROC-AUC** and **0.4053 average precision**. I did not use post-return fields to improve this estimate.

## How do you know it works? How you validated, on what split, error rate, and the kind of case it gets wrong.

I used an order-level deduplicated, chronological split rather than a random split. The validation set contains **2,101 future orders** beginning **2026-04-02** with an **11.52% return rate**.

Metrics:
- ROC-AUC: 0.7795
- Average precision: 0.4053
- Log loss: 0.2975
- Accuracy at 0.50 threshold: 89.24%
- Error rate at 0.50 threshold: 10.76%
- Precision at 0.50 threshold: 76.67%
- Recall at 0.50 threshold: 9.50%

At the operational 0.12 score threshold, 632 validation orders would have been flagged; precision was about **25.0%** and recall about **65.3%**. This reinforces that the model is better treated as a ranking/prioritisation tool than as a binary automatic-cancellation rule.

The common failure mode is a false negative: some genuinely returned orders look normal from the dispatch-time fields, so the model cannot identify them confidently before shipment. False positives are fewer among the high-confidence 0.50 predictions, but they still occur around certain product/channel/payment combinations.

## Did you change, narrow, or push back on the client's ask? What, when, and why?

Yes. I narrowed the success criterion from "95% accuracy" to a **dispatch-safe ranking problem** and explicitly avoided using fields that are created after the return process has started. A leakage-heavy version using service/pickup fields looked almost perfect (about **0.998 ROC-AUC**), but those fields are not valid before-dispatch signals, so I discarded that approach.

I also did not make the model an automatic cancellation rule. The email/policy says extended holds can lead to customer cancellation, but the pack does not provide the rupee value of that cancellation. The system therefore recommends a confirmation/review step rather than inventing a hold-cost model.

## What is wrong with what you are handing us, or with the data we handed you?

- The target is imbalanced: returns are about 11.4% after order-level deduplication, so raw accuracy is misleading.
- The export contains **651 duplicate order rows** caused by partner-feed re-imports; the pipeline canonicalises by `order_id` and prefers the CRM representation.
- `last_service_event_type` and `pickup_scheduled_at` are not trustworthy as pre-dispatch predictors because they can be populated during the return process; they were excluded.
- Some walk-in partner orders legitimately have pincode `000000`, meaning no address was captured.
- The email notes that October festive order values went through a new payment gateway and had not been checked by the exporter; that is a data-quality risk we cannot independently resolve from the supplied pack.
- The policy says legacy resolution timestamps were stored in UTC while other timestamps are displayed in IST. The affected service/resolution fields are not used by the final model.
- The final model does not claim to predict every return. Some returns are driven by information unavailable at dispatch.

## What does one prediction cost, and what would a month cost at Kestrel's volume (about 700 orders a month)? Show the arithmetic. If you used no paid calls, say so.

No paid API calls are used for prediction or explanation.

Variable model/API cost per prediction: **₹0**

Approximate variable model/API cost for 700 orders/month:

**700 × ₹0 = ₹0/month**

This excludes existing infrastructure, electricity, engineering time, or any future hosting cost. The shipped application is designed to run locally without a paid model API key.

## What did you deliberately leave out, and why that rather than something else?

- `last_service_event_type`: may describe a return/service process that has already started.
- `pickup_scheduled_at`: written when reverse pickup is booked after a return is approved.
- `order_id` as a predictive feature: it is an identifier, not an operational signal.
- Any post-return or hold-outcome information: unavailable at dispatch and therefore leakage.
- A generative LLM explanation layer: deterministic model-contribution explanations were sufficient, cheaper, local, and easier for an operations user to audit.

## Anything you built or found that nobody asked for?

Yes:
- Local SQLite prediction logging for basic auditability.
- Automated submission checks for row count, uniqueness, missing scores, score range, and exact column shape.
- A leakage diagnostic comparing a deliberately invalid model against the dispatch-safe model.
- A small evidence report capturing data checks, validation metrics, and failure modes.

## What did you use AI for? Which tools and models, where they helped, where they misled you, what you threw away. Link your three-minute screen recording here.

I used **ChatGPT** for implementation assistance, debugging, code review, and structuring the take-home. It helped with the FastAPI structure, feature-pipeline checks, testing strategy, and documentation.

No Gemini or Groq API is required by the product. I intentionally did not add an external LLM into the prediction path because it would add cost/dependency without improving the core tabular decision.

The main thing I discarded was a leakage-heavy modelling approach that made the validation score look nearly perfect by using service/pickup information that is written during the return process. I also discarded an LLM-generated explanation layer in favour of deterministic model-contribution reasons.

Three-minute screen recording:

`<PUBLIC_SCREEN_RECORDING_LINK>`

Public Google Drive link:

`<PUBLIC_GOOGLE_DRIVE_LINK>`

## Someone picks this up on Monday and you are unreachable. The three things they need to know.

1. **Do not add service/pickup fields back into the model.** They leak information from the return process and invalidate the pre-dispatch decision.
2. **Treat the score as a ranking/prioritisation signal, not a promise of 95% binary accuracy.** The current clean future-period ROC-AUC is about 0.78.
3. **The current working business threshold is around 12% for a confirmation/review step.** The policy's ₹1,150 return cost and ₹45 confirmation call imply a rough break-even risk of about 11.2% under the stated 35% pilot prevention rate.
