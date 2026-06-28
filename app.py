from fetch_cet import cetDATA
from compute_cet import ComputeCET
from get_fcst_runtime import get_fcst_time
import numpy as np
from months import days_in_month
import matplotlib
matplotlib.use('Agg')  # must be before importing pyplot
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

from dash import Dash, html, dcc, callback, Output, Input
import plotly.graph_objects as go
from flask_caching import Cache

app = Dash()

CET_TYPE = ['mean', 'max', 'min']

MONTH = datetime.now().strftime('%B')
NEXT_MONTH = datetime(2000, (datetime.now().month % 12 + 1), 1).strftime('%B')
MONTHS = [MONTH, NEXT_MONTH]
MODELS = {'EC': ["ecmwf_aifs025_single"]}

app.layout = [
    html.H1(children='CET tracker', style={'textAlign':'center'}),
    html.P('Dashed line is observed CET and solid line is the forecast CET.'),
    html.Div([
        dcc.Dropdown(CET_TYPE, 'mean', id='dropdown-selection1', clearable=False),
        dcc.Dropdown(MONTHS, MONTH, id='dropdown-selection2', clearable=False),
    ], style={'display': 'flex', 'gap': '10px'}),
    dcc.Graph(id='graph-content')
]

cache = Cache(app.server, config={
    'CACHE_TYPE': 'SimpleCache',  # in-memory, fine for single user
    'CACHE_DEFAULT_TIMEOUT': 300  # seconds
})

@cache.memoize()
def get_cet_data(month, models, cet_type):
    process_cet = ProcessCET(month, models, cet_type, use_prev=0, full_run=True)
    return process_cet.nwp_cet_data()

@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection1', 'value'),
    Input('dropdown-selection2', 'value')
)

def update_graph(cet_type, month):

    fig = go.Figure()
    fig.update_layout(height=500)  

    if month == MONTH:
        dff_obs, dff_fcst, cet_predict, runtime, tot_days = get_cet_data(month, MODELS, cet_type)
        fig.add_trace(go.Scatter(
            x=dff_obs['cet_dates'],
            y=dff_obs['cet_vals'],
            mode='lines',
            name='Observed',
            line=dict(color='black', dash='dash'),
            hovertemplate='%{y}°C<extra></extra>'
        ))
    else:
        dff_fcst, cet_predict, runtime, tot_days = get_cet_data(month, MODELS, cet_type)

    fig.add_trace(go.Scatter(
        x=dff_fcst['fcst_dates'],
        y=dff_fcst['fcst_vals'],
        mode='lines',
        name='Forecast',
        line=dict(color='red'),
        hovertemplate=f'%{{y}}°C<br>{runtime}<extra></extra>'
    ))

    fig.update_layout(title=f'{month} 2026 CET estimate: {cet_predict:.1f} C (to {tot_days}) (ECMWF AIFS)', xaxis_title='Day', yaxis_title=f'Daily {cet_type} CET (C)')
    fig.update_xaxes(
        range=[1, days_in_month[month]['days']],
        tickvals=[1, 5, 10, 15, 20, 25, days_in_month[month]['days']])
    

    return fig


class ProcessCET():
    """
    Main script for processing both observed and forecast CET data.

    fetch_cet_data: Collects observed CET data, with flag to whether yesterday's CET data has
                    arrived yet.
    nwp_cet_data:   Collects and processes the forecasted CET data, while also splitting up
                    the dates to ensure the predicted CET is a blend of observed and forecasted
                    values (sometimes messy when using previous runs and there is significant
                    overlap). Optional tools for plotting.
    """

    def __init__(self, 
                 month, 
                 models, 
                 cet_type, 
                 plot=False, 
                 use_prev=0, 
                 full_run=True,
                 ):

        self.month = month
        self.models = models
        self.cet_type = cet_type
        self.use_prev = use_prev
        self.full_run = full_run

        self.plot = plot
        if self.plot:
            self.fig, self.ax = plt.subplots(figsize=(12, 8))


    def fetch_cet_data(self):

        cet_data = cetDATA()

        cet_data.fetch_data(self.month, self.cet_type)

        self.cet_in_flag = cet_data.cet_in_flag
        self.cet_vals = cet_data.cet_vals
        self.cet_days = cet_data.cet_days

    def nwp_cet_data(self):

        if self.month != MONTH:

            self.cet_in_flag = False
        
        else:
            
            self.fetch_cet_data()

            print(f"Fetched CET for month {self.month}. {self.cet_vals} for {self.cet_days} days.")

        self.nwp_cet = ComputeCET(self.cet_type, 
                                  self.cet_in_flag, 
                                  self.use_prev, 
                                  self.full_run,
                                  self.month
                                  )
        
        save_str = f"plots/test_{self.month}_{self.cet_type}"

        self.fig, self.ax = plt.subplots(figsize=(12, 8))

        for group, model_array in self.models.items():
        
            for model in model_array:

                runtime=get_fcst_time(model)
                
                self.nwp_cet.fetch_data(model, runtime)
                
                print(f"Computed mean CET: {self.nwp_cet.cet}")

                model_runtime = self.nwp_cet.runtime

                # How many days in total do we (may not be number of days in the month)
                if self.month != MONTH:
                    tot_days = self.nwp_cet.days_fcst + self.nwp_cet.day_of_start
                else:
                    tot_days = self.cet_days + (self.nwp_cet.days_fcst - self.cet_days) + self.nwp_cet.day_of_start
                    if tot_days < self.cet_days:
                        tot_days = self.cet_days
                
                    days_ahead_of_cet = self.nwp_cet.days_fcst + self.nwp_cet.day_of_start - self.cet_days
                    print(f"Total days of data: {tot_days}")
                    print(f"Forecast days ahead of CET date: {days_ahead_of_cet}")
            
                assert tot_days <= days_in_month[self.month]['days'], (
                    f"total_days={tot_days} exceeds days in month "
                    f"({days_in_month[self.month]['days']})"
                )

                nwp_cet_filter = self.nwp_cet.cet

                if self.use_prev and self.cet_in_flag:
                    if days_ahead_of_cet > 0:
                        nwp_cet_filter = self.nwp_cet.cet[self.use_prev:]
                        self.fcst_start = self.cet_days + 1 - self.use_prev
                    else:
                        # if no NWP data is ahead of CET data, we don't 
                        # use it in final prediction
                        nwp_cet_filter = 0
                        self.fcst_start = self.cet_days + 1 - self.use_prev
                elif self.month != MONTH:
                    nwp_cet_filter = self.nwp_cet.cet
                    self.fcst_start = self.nwp_cet.day_of_start+1
                else:
                    nwp_cet_filter = self.nwp_cet.cet
                    self.fcst_start = self.cet_days+1

                # final CET computation, using current CET and fcst CET
                if self.month != MONTH:
                    cet_vals_all = np.sum(nwp_cet_filter)
                else:
                    cet_vals_all = np.sum(self.cet_vals) + np.sum(nwp_cet_filter)
                    dates_cet = np.linspace(1, self.cet_days, self.cet_days, endpoint=True)
                    obs_df = pd.DataFrame({
                        'cet_dates': dates_cet,
                        'cet_vals': self.cet_vals,
                    })
                
                cet_vals_all = cet_vals_all / tot_days
                dates_fcst = np.linspace(self.fcst_start, self.fcst_start + self.nwp_cet.days_fcst - 1, self.nwp_cet.days_fcst, endpoint=True)
                
                fcst_df = pd.DataFrame({
                    'fcst_dates': dates_fcst,
                    'fcst_vals': self.nwp_cet.cet,
                })
                
        if self.month == MONTH:
            return obs_df, fcst_df, cet_vals_all, model_runtime, tot_days
        else:
            return fcst_df, cet_vals_all, model_runtime, tot_days

if __name__ == '__main__':
    app.run(debug=True)