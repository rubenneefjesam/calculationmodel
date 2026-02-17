#!/usr/bin/env bash

# Gebruik:
#   bash scripts/show_results.sh 1
# of
#   ./scripts/show_results.sh 1

GEBOUW_ID=$1

if [ -z "$GEBOUW_ID" ]; then
  echo "Gebruik: ./scripts/show_results.sh <gebouw_id>"
  exit 1
fi

FILE="data/output/results_summary_gebouw_${GEBOUW_ID}.json"

if [ ! -f "$FILE" ]; then
  echo "Result file niet gevonden: $FILE"
  exit 1
fi

echo ""
echo "=============================================="
echo "RESULTATEN VOOR GEBOUW $GEBOUW_ID"
echo "=============================================="
echo ""

echo ">>> GOEDKOOPSTE 10"
echo "----------------------------------------------"
jq -r '.goedkoopste_10[] | 
  "\(.scenario_id)\t€ \(.totaal_prijs)\tCO2: \(.totaal_co2)"' "$FILE"

echo ""
echo ">>> DUURSTE 10"
echo "----------------------------------------------"
jq -r '.duurste_10[] | 
  "\(.scenario_id)\t€ \(.totaal_prijs)\tCO2: \(.totaal_co2)"' "$FILE"

echo ""
echo ">>> LAAGSTE CO2 10"
echo "----------------------------------------------"
jq -r '.laagste_co2_10[] | 
  "\(.scenario_id)\t€ \(.totaal_prijs)\tCO2: \(.totaal_co2)"' "$FILE"

echo ""
echo "=============================================="
