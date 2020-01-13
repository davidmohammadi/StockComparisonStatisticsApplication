import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pandas_datareader.data import DataReader
from datetime import date, datetime

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State

# ===== backend code =====
start_date = '2015-01-01'
end_date = '2020-01-01'
data_provider = 'yahoo'

# fig = make_subplots(rows=2, cols=1, specs=[[{}], [{}]],
#                         shared_xaxes=True, shared_yaxes=False,
#                         vertical_spacing=0.03, )
#
#     fig.append_trace(trace_stock_1, 1, 1)
#     fig.append_trace(trace_stock_2, 2, 1)
#     fig['layout'].update(height=600, title='Stacked Subplots with Shared X-Axes')
#     fig.update_layout(legend_orientation="h")

# ===== initialize the app =====
app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H2("Stock Statistics Application created by David Mohammadi"),
        html.Img(src='/assets/dm_headshot.jpg')
    ], className="banner"),

    html.Div([
        html.Div([
            dcc.Graph(
                id='2-stock-subplot'),
        ])
    ]),
    html.Div([
        dcc.Input(
            id="stock2-input",
            value="^GSPC",
            type="text",
        ),
        dcc.Input(
            id="stock1-input",
            value="MSFT",
            type="text",
        ),
    ]),
])

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})


@app.callback(
    dash.dependencies.Output("2-stock-subplot", "figure"),
    [dash.dependencies.Input("stock1-input", "value"), dash.dependencies.Input("stock2-input", "value")],
)
def update_fig(input_stock_1, input_stock_2):
    df_stocks = pd.DataFrame()
    list_of_companies = [input_stock_2, input_stock_1]

    for company in list_of_companies:
        df = DataReader(name=company,
                        data_source=data_provider,
                        start=start_date,
                        end=end_date).reset_index()
        df["ticker"] = company
        df_stocks = pd.concat([df_stocks, df])

    df_stocks.reset_index(drop=True, inplace=True)

    df_stock_price = pd.pivot(df_stocks, index='Date', columns='ticker', values='Close')
    df_stock_price = pd.DataFrame(df_stock_price.to_records())
    df_stock_price.set_index('Date', inplace=True)

    # ===== Create dash graph objects =====
    trace_stock_1 = go.Scatter(x=list(df_stock_price.index),
                               y=list(df_stock_price.iloc[:, 1]),
                               name=list_of_companies[0],
                               line=dict(color='blue'))

    trace_stock_2 = go.Scatter(x=list(df_stock_price.index),
                               y=list(df_stock_price.iloc[:, 0]),
                               name=list_of_companies[1],
                               line=dict(color='red'))

    fig = make_subplots(rows=2, cols=1, specs=[[{}], [{}]],
                        shared_xaxes=True, shared_yaxes=False,
                        vertical_spacing=0.07, subplot_titles=[input_stock_1, input_stock_2])

    fig.append_trace(trace_stock_1, 2, 1)
    fig.append_trace(trace_stock_2, 1, 1)
    fig['layout'].update(height=600,
                         # title="Graph Comparison: " + str(list_of_companies[0] + " & " + str(list_of_companies[1])),
                         )
    fig.update_layout(legend_orientation="h")

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
