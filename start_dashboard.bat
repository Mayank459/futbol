@echo off
title Football Value-Betting Dashboard (Keep-Alive Watchdog)
echo Starting Football Value-Betting Agent Dashboard...
echo Target Bookmaker: Stake (stake.ac)
echo URL: http://localhost:8501
start http://localhost:8501
python keep_alive.py
pause

