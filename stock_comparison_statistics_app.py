import pandas as pd
import numpy as np
from datetime import date, datetime

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pandas_datareader.data import DataReader

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State


# ===== backend code =====
def pull_stock_data(input_stock_1, input_stock_2, input_date_start, input_date_end):
    df_stocks = pd.DataFrame()
    data_provider = 'yahoo'

    # Inputted from callback
    list_of_companies = [input_stock_2, input_stock_1]
    start_date = input_date_start
    end_date = input_date_end

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

    return df_stock_price


def create_financial_statistics(start_date, end_date, df_stocks, list_of_companies, risk_free_rate_percent):
    list_of_companies_reversed = list([list_of_companies[1], list_of_companies[0]])
    df_fin_stats = pd.DataFrame(columns=list_of_companies_reversed)
    df_stock_returns = df_stocks.pct_change()

    # Calculate time-frame
    from_date_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_datetime = datetime.strptime(end_date, "%Y-%m-%d")
    years = ((end_date_datetime - from_date_datetime).days / 365)

    # Total Return
    list_total_percent_return = []
    df_total_return = pd.DataFrame(columns=df_stocks.columns)
    for i in range(len(df_stocks.columns)):
        list_total_percent_return.append(
            (df_stocks.iloc[-1, i] - df_stocks.iloc[0, i]) / df_stocks.iloc[0, i])

    df_total_return.loc[len(df_total_return)] = list_total_percent_return
    df_fin_stats = pd.concat([df_fin_stats, df_total_return])

    # Annualized Return
    df_annualized_return = (df_total_return + 1) ** (1 / years) - 1
    df_fin_stats = pd.concat([df_fin_stats, df_annualized_return])

    # Annualized Volatility
    df_annualized_vol = (df_stock_returns.std() * np.sqrt(250)).to_frame().transpose()
    df_fin_stats = pd.concat([df_fin_stats, df_annualized_vol])

    # Assumed risk free rate
    risk_free_rate_decimal = risk_free_rate_percent * 0.01

    # Sharpe Ratio
    df_sharpe_ratio = (df_annualized_return - risk_free_rate_decimal) / df_annualized_vol
    df_fin_stats = pd.concat([df_fin_stats, df_sharpe_ratio])

    # Rename DataFrame indexes for readability
    df_fin_stats['Assumed Risk Free Rate: ' +
                 str(risk_free_rate_decimal * 100) + '%'] = ['Total Return (decimal)',
                                                             'Annualized Return (decimal)',
                                                             'Annualized Volatility (decimal)',
                                                             'Sharpe Ratio']
    df_fin_stats = df_fin_stats[
        ['Assumed Risk Free Rate: ' + str(risk_free_rate_decimal * 100) + '%', list_of_companies_reversed[0],
         list_of_companies_reversed[1]]]

    return df_fin_stats


# ===== initialize the app =====
app = dash.Dash(__name__,
                #   external_stylesheets=external_stylesheets
                )

app.layout = html.Div([
    # Header
    html.Div([
        html.H2("Stock Statistics Application created by David Mohammadi (github.com/davidmohammadi)"),
        html.Img(src='/assets/dm_headshot.jpg')
    ], className="banner"),

    # Stock Ticker Input
    html.Div([
        # currently using PlainText for spacing instead of HTML styling
        html.Plaintext(""),
        html.Label(['Stock Tickers:']),
        html.Div([
            dcc.Input(
                id="stock2-input",
                type="text",
                value="^GSPC"
            ),
            dcc.Input(
                id="stock1-input",
                type="text",
                value="MSFT"
            ),
        ]),
        html.Plaintext(""),
        html.Label(['Date Range (YYYY-MM-DD):']),
        html.Div([
            dcc.Input(
                id="start-date-input",
                type="text",
                value='2015-01-01'
            ),
            dcc.Input(
                id="end-date-input",
                type="text",
                value='2020-01-01'
            ),
        ]),
        html.Plaintext(""),
        html.Label([
            html.A("Risk Free Rate (include %):",
                   href='https://www.treasury.gov/resource-center/data-chart-center/interest-rates/pages/textview.aspx?data=yield',
                   target='_blank')
        ]),
        html.Div([
            dcc.Input(
                id="risk-free-rate-string",
                type="text",
                value='1.52%'
            ),
        ]),
        # currently using plaintext for spacing instead of HTML styling
        html.Plaintext(""),
    ], className="stock_input"),

    # Submit button
    html.Div([
        html.Button(
            id='stock-submit-button',
            n_clicks=0,
            children='Submit',
        )
    ], className="ticker-date-submit-button"),

    # Visual Output
    html.Div([
        html.Div([
            dcc.Graph(
                id='2-stock-subplot'),
        ], ),

        html.Div(
            id='2-stock-df',
        ),
    ]),
], style={'padding': '0px 20px 20px 20px'})


@app.callback(
    [Output("2-stock-subplot", "figure"), Output("2-stock-df", "children")],
    [Input("stock-submit-button", "n_clicks")],
    [State("stock1-input", "value"), State("stock2-input", "value"),
     State("start-date-input", "value"), State("end-date-input", "value"),
     State("risk-free-rate-string", "value")],
)
def update_fig(n_clicks, input_stock_1, input_stock_2, input_date_start, input_date_end, risk_free_rate_string):
    df_stock_price = pull_stock_data(input_stock_1=input_stock_1, input_stock_2=input_stock_2,
                                     input_date_start=input_date_start,
                                     input_date_end=input_date_end)
    list_of_companies = [input_stock_2, input_stock_1]

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
    fig['layout'].update(height=600, width=1200)
    fig.update_layout(legend_orientation="h")

    risk_free_rate_percent = float(risk_free_rate_string[0:-1])

    df_fin_stats = (
        create_financial_statistics(start_date=input_date_start, end_date=input_date_end, df_stocks=df_stock_price,
                                    list_of_companies=list_of_companies, risk_free_rate_percent=risk_free_rate_percent))

    return fig, html.Div([
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in df_fin_stats.columns],
            data=df_fin_stats.to_dict("rows"),
            style_table={'width': '1000px',
                         'textAlign': 'center'},
            style_as_list_view=True,
            style_header={
                'backgroundColor': 'white',
                'fontWeight': 'bold'
            },
            style_cell_conditional=[
                {
                    'textAlign': 'center'
                }
            ],
            style_cell=
            {
                'font_size': '16px'
            }

        )
    ])


if __name__ == "__main__":
    app.run_server(debug=True)
