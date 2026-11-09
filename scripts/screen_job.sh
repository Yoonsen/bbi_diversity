#!/usr/bin/env bash
# Start a long-running job on a remote server in a detached screen session.
#   scripts/screen_job.sh <name> <python-script-and-args...>
# Runs from ~/bbi_diversity with .venv, in a login shell, and logs to logs/<name>.log.
# API keys: taken from the login shell, plus ~/.config/bbi/keys.env if it exists
# (lines like `export GEMINI_API_KEY=...`, chmod 600). Never commit that file.
set -euo pipefail
name="$1"; shift
cd ~/bbi_diversity
mkdir -p logs
cmd=$(printf '%q ' "$@")
screen -dmS "bbi_$name" bash -lic "
  [ -f ~/.config/bbi/keys.env ] && source ~/.config/bbi/keys.env
  cd ~/bbi_diversity
  echo \"start \$(date -Is)\" >> logs/$name.log
  .venv/bin/python -u $cmd >> logs/$name.log 2>&1
  echo \"slutt \$(date -Is) status \$?\" >> logs/$name.log
"
echo "startet screen-økt bbi_$name, logg: ~/bbi_diversity/logs/$name.log"
