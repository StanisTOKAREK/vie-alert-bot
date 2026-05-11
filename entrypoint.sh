#!/bin/bash
# Script to run the bot every hour indefinitely

echo "V.I.E Alert Bot started on Fly.io"
echo "Will run every hour at the top of the hour"

while true; do
    # Run the bot
    /opt/miniconda3/envs/vie-alert/bin/python /app/run_check.py --hourly
    
    # Wait 1 hour before next run
    echo "Waiting 3600 seconds until next check..."
    sleep 3600
done
