@echo off
title Smart Cane Capstone Demo (PW_27_MHR_01)
echo ======================================================================
echo  PES UNIVERSITY - CAPSTONE ESA DEMO (PW_27_MHR_01)
echo  Smart Cane for Near-Fall Detection: Cane Kinematics & Grip Dynamics
echo  Guide: Dr. Mamatha H R
echo  Team: Tanisha Mathur, Samika Ojha, Saatvik Gupta, Pratham S Reddy
echo ======================================================================
echo.
echo Starting demonstration server and launching browser...
echo.

cd /d "%~dp0\..\.."
python capstone\demo\server.py

pause
