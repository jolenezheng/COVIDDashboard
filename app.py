# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
from dash.dependencies import Output, Input
import plotly.express as px
import plotly.graph_objects as go
import datetime as dt

from textwrap import dedent


data = pd.read_csv("avocado.csv")
data["Date"] = pd.to_datetime(data["Date"], format="%Y-%m-%d")
data.sort_values("Date", inplace=True)

df_mort = pd.read_csv('https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_hr/mortality_timeseries_hr.csv')
df_mort["date_death_report"] = pd.to_datetime(df_mort["date_death_report"], format="%d-%m-%Y")

weather_base_url = 'https://dd.weather.gc.ca/climate/observations/daily/csv/'

df_mob = pd.read_csv('https://www.gstatic.com/covid19/mobility/Global_Mobility_Report.csv')


external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]
fnameDict = {    
    "Alberta": ["Calgary","Central","Edmonton","North","Not Reported","South"], 
    "British Columbia":["Fraser","Interior","Island","Northern","Not Reported","Vancouver Coastal"],
    "Manitoba": ["Interlake-Eastern","Northern","Not Reported","Prairie Mountain","Southern Health","Winnipeg"],
    "New Brunswick": ["Not Reported","Zone 1 (Moncton area)","Zone 2 (Saint John area)","Zone 3 (Fredericton area)",
                      "Zone 4 (Edmundston area)","Zone 5 (Campbellton area)","Zone 6 (Bathurst area)","Zone 7 (Miramichi area)"],
    "Newfoundland and Labrador": ["Central","Eastern","Labrador-Grenfell", "Not Reported","Western"],
    "Nunavut": ["Nunavut"], "Northwest Territories": ["NWT"], "Ontario": ["Algoma","Brant","Chatham-Kent","Durham","Eastern",
                "Grey Bruce","Haldimand-Norfolk","Haliburton Kawartha Pineridge","Halton","Hamilton","Hastings Prince Edward",
                "Huron Perth","Kingston Frontenac Lennox & Addington","Lambton","Leeds Grenville and Lanark","Middlesex-London",
                "Niagara","North Bay Parry Sound","Northwestern","Not Reported","Ottawa","Peel","Peterborough","Porcupine",
                "Renfrew","Simcoe Muskoka","Southwestern","Sudbury","Thunder Bay","Timiskaming","Toronto","Waterloo",
                "Wellington Dufferin Guelph","Windsor-Essex","York"], "Prince Edward Island": ["Prince Edward Island"],
    "Quebec": ["Estrie","Not Reported","Nunavik","Outaouais","Saguenay","Terres-Cries-de-la-Baie-James"],
    "Repatriated": ["Not Reported"], "Saskatchewan":["Central","Far North","North","Not Reported","Regina","Saskatoon","South"],
    "Yukon": ["Yukon"]
}

names = list(fnameDict.keys())
nestedOptions = fnameDict[names[0]]
tempSubregion = "Northern"

base_intro = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, \
    sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. \
        Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris \
            nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor \
                in reprehenderit in voluptate velit esse cillum dolore eu \
                    fugiat nulla pariatur. Excepteur sint occaecat cupidatat \
                        non proident, sunt in culpa qui officia deserunt mollit \
                            anim id est laborum.
"""

extend_intro = """This app was created to act as an interface for an Ocean Optics
spectrometer. Use controlling elements to control various
properties of the instrument; the integration time, the number of
scans to average over, the strobe and strobe period, and the
light source.

Clicking "Update" after putting in the desired settings will
result in your parameter settings being sent to the device. A status message
will appear below the button indicating which commands, if any,
were unsuccessful; below the unsuccessful commands, a list of
successful commands can be found.
           
The dial labelled "Light intensity" will affect the current
selected light source, if any. The switch labelled autoscale
plot will change the axis limits of the plot to fit all of the
data. Please note that the animations and speed of the graph will
improve if this autoscale is turned off, and that it will not be
possible to zoom in on any portion of the plot if it is turned
on.
"""

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "COVID Dashboard"


app.layout = html.Div(
    children=[
        html.Div(
            id="banner",
            className="banner",
            children="COVID Dashboard",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Daily Mortality", className="options-header"),
                        html.Div(
                            children=[
                                html.Div(children="Region", className="dropdown-title"),
                                dcc.Dropdown(
                                    id='region-dropdown',
                                    className='dropdown',
                                    options=[{'label':name, 'value':name} for name in names],
                                    value = list(fnameDict.keys())[0]
                                ),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Div(children="Sub-Region", className="dropdown-title"),
                                dcc.Dropdown(
                                    id='subregion-dropdown',
                                    className='dropdown',
                                    value = 'None'
                                ),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Div(
                                    children="Date Range",
                                    className="dropdown-title"
                                    ),
                                dcc.DatePickerRange(
                                    id="date-range",
                                    min_date_allowed=df_mort.date_death_report.min().date(),
                                    max_date_allowed=df_mort.date_death_report.max().date(),
                                    start_date=df_mort.date_death_report.min().date(),
                                    end_date=df_mort.date_death_report.max().date(),
                                ),
                            ]
                        ),
                    ],
                    className="options-card",
                ),
                html.Div(
                    children=[
                        html.Div(children="Weather Data", className="options-header"),
                        html.Div(
                            children=[
                                html.Div(children="Province", className="dropdown-title"),
                                dcc.Dropdown(
                                    id='weather-prov-dropdown',
                                    className='dropdown',
                                    options=[{'label':name, 'value':name} for name in names],
                                    value = list(fnameDict.keys())[0]
                                ),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Div(children="Station ID", className="dropdown-title"),
                                dcc.Dropdown(
                                    id='weather-id-dropdown',
                                    className='dropdown',
                                    options=[{'label': '3031092', 'value': '3031092'}],
                                    # options=[{'label':name, 'value':name} for name in names],
                                    # value = list(fnameDict.keys())[0]
                                ),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Div(
                                    children="Date Range",
                                    className="dropdown-title"
                                    ),
                                dcc.DatePickerRange(
                                    id="weather-date-range",
                                    min_date_allowed=df_mort.date_death_report.min().date(),
                                    max_date_allowed=df_mort.date_death_report.max().date(),
                                    start_date=df_mort.date_death_report.min().date(),
                                    end_date=df_mort.date_death_report.max().date(),
                                ),
                            ]
                        ),
                    ],
                    className="options-card",
                ),
            ],
            className="left-column columns",
        ),
        html.Div(
            children=[
                dcc.Markdown(
                    dedent(base_intro), id="graph-title-intro"
                ),
                # html.Button(
                #     "Learn More", id="learn-more-btn", n_clicks=0
                # ),
                html.Div(
                    children=[
                        html.Div(children="Daily Mortality Graph", className="options-header"),
                        html.Div(
                            children=dcc.Graph(
                                id="covid-chart", config={"displayModeBar": False},
                            ),
                            className="card",
                        ),
                        html.Div(children="Weather Graph", className="options-header"),
                        html.Div(
                            children=dcc.Graph(
                                id="weather-chart", config={"displayModeBar": False},
                            ),
                            className="card",
                        ),
                    ],
                ),
            ],
            className="right-column columns",
        ),
    ]
)

@app.callback(
    dash.dependencies.Output('subregion-dropdown', 'options'),
    [dash.dependencies.Input('region-dropdown', 'value')]
)

def update_date_dropdown(name):
    return [{'label': i, 'value': i} for i in fnameDict[name]]


# ============== MORTALITY GRAPH ==============
@app.callback(
    Output("covid-chart", "figure"),
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_covid_chart(name, region, start_date, end_date):
    print(start_date)
    print(end_date)
    if (name == "Newfoundland and Labrador"):
        name = "NL"
    elif (name == "British Columbia"):
        name = "BC"

    fig = px.line(df_mort, x = date(name, region, start_date, end_date), y = r_avg(name, region, start_date, end_date))

    fig.update_layout(title='Daily Reported Deaths in ' + region + ', ' + name,
                   xaxis_title='Date',
                   yaxis_title='Daily Mortality (7-day Rolling Average)')

    return fig


# ============== WEATHER GRAPH ==============
@app.callback(
    Output("weather-chart", "figure"),
    [
        Input("weather-prov-dropdown", "value"),
        Input("weather-id-dropdown", "value"),
        Input("weather-date-range", "start_date"),
        Input("weather-date-range", "end_date"),
    ],
)
def update_weather_chart(prov, station_id, start_date, end_date):
    if (prov == "Newfoundland and Labrador"):
        namprove = "NL"
    elif (prov == "British Columbia"):
        prov = "BC"

    prov = "AB"
    station_id = "3031092";
    date_rang = "2016-12"
    # date_rang = date(2016,12,1).strftime("%Y-%m")


    # target_url = weather_base_url + prov + '/climate_daily_' + prov+ '_' +station_id+ '_' +date_rang+ '_P1D.csv'
    # weat_data =  pd.read_csv(target_url, encoding='Latin-1')

    # weat_city = weat_data['Mean Temp (•C)']
    # date_city = weat_data['Date/Time']

    x = np.arange(10)

    fig = px.line(df_mort, x = x, y = x*x*2)
    # fig = px.line(df_mort, x = date_city, y = weat_city)

    # fig = go.Figure(data=go.Scatter(x=date_city, y=weat_city))
    # fig = px.line(df_mort, x = date(prov, region, start_date, end_date), y = r_avg(prov, region, start_date, end_date))

    fig.update_layout(title='Daily Reported Temperature in ' + prov,
                   xaxis_title='Date',
                   yaxis_title='Mean Temperature')

    return fig



def date(province_name, region_name, start_date, end_date):

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    filtered_df = df_mort[df_mort.date_death_report.between(
        dt.datetime.strftime(start_date, "%d-%m-%Y"),
        dt.datetime.strftime(end_date, "%d-%m-%Y")
    )]
    
    df_province = filtered_df[filtered_df.province == province_name]
    return df_province.date_death_report[df_province.health_region == region_name]
    

def r_avg(province_name, region_name, start_date, end_date):

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    filtered_df = df_mort[df_mort.date_death_report.between(
        dt.datetime.strftime(start_date, "%d-%m-%Y"),
        dt.datetime.strftime(end_date, "%d-%m-%Y")
    )]
    
    df_province = filtered_df[filtered_df.province == province_name]
    return df_province.deaths[df_province.health_region == region_name].rolling(window=7).mean()


def display_info_box(btn_click):
    if (btn_click % 2) == 1:
        return dedent(extend_intro), "Close"
    else:
        return dedent(base_intro), "Learn More"


if __name__ == "__main__":
    app.run_server(debug=True)
