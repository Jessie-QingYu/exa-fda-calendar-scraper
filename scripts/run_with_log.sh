mkdir -p logs

TS=$(date +"%Y%m%d_%H%M%S")

LOGFILE="logs/run_${TS}.log"

echo "==> Running FDA calendar scraper..."
echo "==> Log will be saved to $LOGFILE"

python -m exa_fda_calendar.cli --sources all --livecrawl always --min-structured 3 --save-raw | tee "$LOGFILE"

echo "==> Done. Full log saved at $LOGFILE"
