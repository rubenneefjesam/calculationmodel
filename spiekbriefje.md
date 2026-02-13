# Spiekbriefje — Calculationmodel Pipeline

## 1) CSV → JSONL (materials)
python scripts/convert_csv_to_jsonl.py materials.csv materials.jsonl

(Indien gebouwgegevens ook uit CSV komen)
python scripts/convert_csv_to_jsonl.py gebouwgegevens.csv gebouwgegevens.jsonl


## 2) Scenario’s genereren
python scripts/generate_scenarios.py --materials materials.jsonl --out scenarios.jsonl

(Optioneel subset testen)
python scripts/generate_scenarios.py --materials materials.jsonl --out scenarios.jsonl --include Beglazing Gevelisolatie


## 3) Results berekenen voor 1 gebouw
python scripts/compute_results.py --gebouw-id 1

(Optioneel custom outputnaam)
python scripts/compute_results.py --gebouw-id 1 --out scenario_results_gebouw_1.jsonl


## 4) Top resultaten bekijken
python scripts/rank_results.py --results scenario_results_gebouw_1.jsonl

Top 10:
python scripts/rank_results.py --results scenario_results_gebouw_1.jsonl --top 10

(Als rank_results.py met gebouw-id is aangepast)
python scripts/rank_results.py --gebouw-id 1


## 5) 1 scenario detailberekening tonen
python scripts/explain_scenario.py --gebouw-id 1 --scenario-id 3
