@echo off
echo.
echo  Hidani Tech -- AI Job Assistant Backend
echo  Starting FastAPI on http://localhost:8000
echo.
cd /d %~dp0
python -X utf8 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
