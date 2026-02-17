# Spiekbriefje — Calculationmodel Pipeline (nieuwe mappenstructuur)

Projectstructuur:
- data/bronddata/
- data/gebouwdata/
- data/output/
- scripts/


## 1) CSV → JSONL (materials)

Materials:
python scripts/convert_csv_to_jsonl.py data/bronddata/materials.csv data/bronddata/materials.jsonl

Gebouwgegevens (indien nodig):
python scripts/convert_csv_to_jsonl.py data/gebouwdata/gebouwgegevens.csv data/gebouwdata/gebouwgegevens.jsonl


## 2) Scenario’s genereren

python scripts/generate_scenarios.py \
  --materials data/bronddata/materials.jsonl \
  --out data/output/scenarios.jsonl

(Optioneel subset testen)
python scripts/generate_scenarios.py \
  --materials data/bronddata/materials.jsonl \
  --out data/output/scenarios.jsonl \
  --include Beglazing Gevelisolatie


## 3) Results berekenen voor 1 gebouw

python scripts/compute_results.py \
  --materials data/bronddata/materials.jsonl \
  --scenarios data/output/scenarios.jsonl \
  --buildings data/gebouwdata/gebouwgegevens.jsonl \
  --gebouw-id 1 \
  --out data/output/scenario_results_gebouw_1.jsonl


## 4) Top resultaten bekijken

python scripts/rank_results.py \
  --results data/output/scenario_results_gebouw_1.jsonl

Top 10:
python scripts/rank_results.py \
  --results data/output/scenario_results_gebouw_1.jsonl \
  --top 10


## 5) 1 scenario detailberekening tonen

python scripts/explain_scenario.py \
  --materials data/brondata/materials.jsonl \
  --scenarios data/output/scenarios.jsonl \
  --buildings data/gebouwdata/gebouwgegevens.jsonl \
  --gebouw-id 1 \
  --scenario-id 3
