# Kestrel Home - Returns Risk (Variant A)

A small, local pre-dispatch return-risk service for the Kestrel Home take-home assignment.

## What it does

- Trains a CatBoost classifier on historical orders.
- Uses only information available at dispatch.
- Generates `predictions.csv` in the required `order_id,score` shape.
- Serves one prediction endpoint with an estimated risk score and human-readable reasons.
- Includes a polished HTML/CSS/JavaScript operations screen with restrained motion and no frontend build step.
- Logs predictions to a local SQLite database.

## Important data decision

`last_service_event_type` and `pickup_scheduled_at` are intentionally excluded from the model. Kestrel's policy says these can be written after a return is raised/approved, so using them would leak the outcome into a pre-dispatch model.

The training export also contains partner-feed re-imports. The training pipeline collapses duplicate `order_id` values and prefers the CRM copy when both sources exist.

## Data setup

The supplied client pack is mirrored under `data/` for local execution and under `client_pack/` in the final private handoff ZIP. Keep the GitHub repository private. Put the supplied files in `data/` with these exact names:

- `train.csv`
- `test_unlabelled.csv`
- `customers.csv`
- `products.csv`
- `sample_submission.csv`

The PDF policy and email thread are included for handoff/documentation; the service only requires the customer/product reference data and the trained local model.

## Run locally

Python 3.11+ is recommended.

```bash
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
python -m scripts.train
python -m scripts.generate_predictions
python -m scripts.validate_submission
pytest -q
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

The browser UI is plain HTML/CSS/JavaScript and runs with no npm install or frontend build step. It uses subtle CSS/JS motion rather than a UI framework so the submission remains easy to start on a clean machine.

No paid API key is required. No external model API is used by the core product.

## API

`POST /api/predict` accepts one order record in the same shape as the test snapshot and returns:

- `score`: higher means more likely to be returned
- `risk_band`: LOW / MEDIUM / HIGH
- `recommended_action`
- `reasons`: employee-readable reasons derived from the model contribution values

## Validation

The primary validation split is chronological rather than random. On the current data, the dispatch-safe model is approximately:

- ROC-AUC: 0.78
- Average precision: 0.41
- Accuracy at 0.5: about 89%

A separate leakage check using service/pickup fields reached about 0.998 ROC-AUC; that model was discarded because those fields can be populated after the return process has started.

## Business interpretation

The policy lists an average return cost of Rs 1,150 and a pre-dispatch confirmation call cost of Rs 45. The pilot reportedly prevented about 35% of returns on called orders. The rough call break-even risk is therefore:

`45 / (0.35 * 1,150) ~= 11.2%`

The service uses a conservative operational banding around that economics rather than automatically cancelling orders.

## Submission form

`submission-answers.md` is a copy-ready draft for the online form. It is not a replacement for the form itself, and there is intentionally no `submission-form.md` in this project.

## AI disclosure

- ChatGPT was used for implementation assistance, debugging and review.
- No paid LLM/API key is required to run this project.
- No LLM is used to invent risk explanations; reasons come from model feature contributions.
- The discarded approach was an LLM-generated explanation layer because it added a dependency without improving the decision path.

## Client-data handling

This repository is intended to remain private. The supplied data must not be published. The `.gitignore` keeps the raw client data out of source control by default.
