@echo off
echo Installing requirements...
pip install -r requirements.txt

echo.
echo Creating required directories...
if not exist pages mkdir pages

echo.
echo Starting Streamlit app...
python -m streamlit run Home.py

pause 