@echo off
echo ========================================================
echo  CNT-02 India E-Commerce Research Suite
echo ========================================================
echo.
echo [1/3] Running Python statistical analysis and generating figures...
python run_project.py

echo.
echo [2/3] Generating executive interactive HTML dashboard...
python generate_dashboard.py

echo.
echo [3/3] Generating comprehensive 23-page PDF project report...
python generate_report.py

echo.
echo ========================================================
echo  All operations completed successfully!
echo  - Report: outputs\CNT02_Project_Report.pdf
echo  - Dashboard: outputs\interactive_dashboard.html
echo ========================================================
pause
