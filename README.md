# CET Tracker and predictor

The driver script is script.py, where models and CET type (maximum, minimum, mean) can be set. Optional to plot too. If models don't extend out to month end, a rolling CET is estimated up to the forecast end date.

Usage:

Install required packages with "pip install -r requirements.txt" in your terminal

Configure underneath __name__=="__main__", then run "python script.py" in your terminal.

Forecast data is sourced from the Open-Meteo API (https://open-meteo.com), released under CC BY 4.0. 
CET data is sourced from United Kingdom Met Office, released under Crown Copyright (no conflict with CC BY 4.0).