# StockComparisonStatisticsApplication
I noticed that it isn't easy to find basic information on a stock over a specified time range. 
Using pandas_datareader and yahoo finance on the backend, this application allows the user to derive some key 
statistics on a stock's price for any valid timeframe.

# Required Python packages
- import pandas as pd
- import numpy as np
- from datetime import date, datetime

- import plotly.graph_objects as go
- from plotly.subplots import make_subplots
- from pandas_datareader.data import DataReader

- import dash
- import dash_table
- import dash_core_components as dcc
- import dash_html_components as html
- from dash.dependencies import Output, Input, State

