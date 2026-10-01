# 3-minute screen-recording script

**0:00-0:25 - What I built**  
"I built a small pre-dispatch return-risk service. It takes the same order snapshot Kestrel sees, scores the return risk, and gives an operations-friendly reason for the score."

**0:25-0:55 - What I tried**  
"I first checked the raw export for duplicates, missing data, class balance and fields that might leak the return outcome. The training export has partner-feed re-imports, so I deduplicated by order ID and kept the CRM representation when available."

**0:55-1:20 - What I changed**  
"The biggest change was removing service and pickup signals. Those fields can be written after the return process starts, so a model using them would not be a real pre-dispatch model."

**1:20-1:55 - Show the model**  
"The final model is CatBoost on dispatch-known order, customer and product features. On a chronological holdout it is around 0.78 ROC-AUC and 0.41 average precision. I did not force the requested 95% accuracy by using leakage."

**1:55-2:35 - Show the app**  
"This screen calls the FastAPI endpoint. I can load an example order, check the score, and see the risk band, recommended next step and the main factors the model used."

**2:35-3:00 - What I threw away**  
"I discarded the leakage-heavy model, random validation, and an LLM explanation layer. The final version is local, reproducible, requires no paid API key, and logs predictions to SQLite."
