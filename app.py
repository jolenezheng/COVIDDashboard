# -*- coding: utf-8 -*-
import math
import pandas as pd
import numpy as np
import datetime as datetime
import urllib.request as request
import random
import requests
import time
import json
import dash
import dash_table
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
#===BPH make the Input, Output, and State calls explicit
#from dash.dependencies import Output, Input, State
import dash.dependencies as ddp
import plotly.express as px
import plotly.graph_objects as go

from textwrap import dedent
from dateutil.relativedelta import relativedelta
from pages import *

import ssl
ssl._create_default_https_context = ssl._create_unverified_context


external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]
# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, external_stylesheets])

# df_mort = pd.read_csv('https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_hr/mortality_timeseries_hr.csv', parse_dates=[0]) #, dayfirst=True)
df_mort = pd.read_csv(r'data/mortality.csv') # ('https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_hr/mortality_timeseries_hr.csv', parse_dates=[0]) #, dayfirst=True)
df_mort["date_death_report"] = pd.to_datetime(df_mort["date_death_report"], format="%d-%m-%Y") #, dayfirst =True)

df_cases = pd.read_csv(r'data/cases.csv') # ('https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_hr/cases_timeseries_hr.csv')
df_cases["date_report"] = pd.to_datetime(df_cases["date_report"], format="%d-%m-%Y") #, dayfirst =True)

#weather_base_url = 'https://dd.weather.gc.ca/climate/observations/daily/csv/' # todo: accented names?
weather_data_dir = "data/weather/all_health_regions_actual_avg_temperature_files/2020-01-01_2023-01-01/"

static_data = pd.read_csv(r'data/health_regions_static_data.csv', encoding='Latin-1')

# mobility_info = pd.read_csv(r'data/mobility_test.csv')
mobility_info = pd.read_csv(r'data/mobility.csv')
mobility_info["sub_region_2"] = mobility_info["sub_region_2"]

df_trends = pd.read_csv(r'data/google_trends_face_mask_canada.csv')

#===BPH added this as variable (set to 10, unless testing)
number_of_simulations = 10

prov_id = "ON"
climate_id = 0
target_url = ""
weat_data = None
weat_city = None
date_city = None
# total_deaths = 0

initial_load = True
prev_states = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]

default_temp = 0.0

#===BPH removed this global variable
#all_temp_vals = []


fnameDict = {    
    "Alberta": ["Calgary","Central","Edmonton","North","South"], 
    "British Columbia":["Fraser","Interior","Island","Northern","Vancouver Coastal"],
    "Manitoba": ["Interlake-Eastern","Northern","Prairie Mountain","Southern Health","Winnipeg"],
    "New Brunswick": ["Zone 1 (Moncton area)","Zone 2 (Saint John area)","Zone 3 (Fredericton area)",
                      "Zone 4 (Edmundston area)","Zone 5 (Campbellton area)","Zone 6 (Bathurst area)","Zone 7 (Miramichi area)"],
    "Newfoundland and Labrador": ["Central","Eastern","Labrador-Grenfell","Western"],
    "Nunavut": ["Nunavut"], "Northwest Territories": ["NWT"], "Nova Scotia": ["Zone 1 - Western","Zone 2 - Northern",
                "Zone 3 - Eastern","Zone 4 - Central"], "Ontario": ["Algoma","Brant","Chatham-Kent","Durham","Eastern",
                "Grey Bruce","Haldimand-Norfolk","Haliburton Kawartha Pineridge","Halton","Hamilton","Hastings Prince Edward",
                "Huron Perth","Kingston Frontenac Lennox & Addington","Lambton","Leeds Grenville and Lanark","Middlesex-London",
                "Niagara","North Bay Parry Sound","Northwestern","Ottawa","Peel","Peterborough","Porcupine",
                "Renfrew","Simcoe Muskoka","Southwestern","Sudbury","Thunder Bay","Timiskaming","Toronto","Waterloo",
                "Wellington Dufferin Guelph","Windsor-Essex","York"], "Prince Edward Island": ["Prince Edward Island"],
    "Quebec": ["Abitibi-Temiscamingue","Bas-Saint-Laurent","Capitale-Nationale",
               "Chaudiere-Appalaches","Cote-Nord","Estrie","Gaspesie-Iles-de-la-Madeleine",
               "Lanaudiere","Laurentides","Laval","Mauricie","Monteregie",
               "Montreal","Nord-du-Quebec","Nunavik",
               "Outaouais","Saguenay","Terres-Cries-de-la-Baie-James"],
    "Saskatchewan":["Central","Far North","North","Regina","Saskatoon","South"],
    "Yukon": ["Yukon"]
}

names = list(fnameDict.keys())
nestedOptions = fnameDict[names[0]]
tempSubregion = "Northern"


server = app.server
app.title = "COVID Dashboard"

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink(html.Img(src='assets/canadian_flag.png', height="20px"), href="/")),
        dbc.NavItem(dbc.NavLink(html.Img(src='assets/usa.png', height="20px"), href="https://www.wolframcloud.com/obj/mohammadb/COVID19Dashboard2", target="_blank")),
        dbc.NavItem(dbc.NavLink("Introduction", href="intro")),
        dbc.NavItem(dbc.NavLink("About Us", href="about")),
        dbc.NavItem(dbc.NavLink("FAQ", href="faq")),
        dbc.NavItem(html.Img(src='assets/waterloo.png', height="40px")),
    ],
    brand="My Local COVID: History, Forecast and Mitigation Portal",
    brand_style={'align':'right'},
    brand_href="/",
    color="dark",
    dark=True,
    fixed="top",
)

navbar2 = dbc.Navbar([
            dbc.Row(
                [
                    dbc.Col(
                        html.Img(src='assets/waterloo.png', height="40px"),
                        width="auto",
                    ),
                    dbc.Col(
                        dbc.NavLink("My Local COVID: History, Forecast and Mitigation Portal", href="/"),
                        width="auto",
                        style={"color": "white", "size":"14px"},
                    ),
                    dbc.Col(
                        dbc.NavLink(html.Img(src='assets/canadian_flag.png', height="20px"), href="/"),
                        width="auto",
                    ),
                    dbc.Col(
                        dbc.NavLink(html.Img(src='assets/usa.png', height="20px"), href="https://www.wolframcloud.com/obj/mohammadb/COVID19Dashboard2", target="_blank"),
                        width="auto",
                    ),
                    dbc.Col(
                        dbc.NavLink("Introduction", href="intro"),
                        width="auto",
                        style={"color": "white !important"}
                    ),
                    dbc.Col(
                        dbc.NavLink("About Us", href="about"),
                        width="auto",
                        style={"color": "white"}
                    ),
                    dbc.Col(
                        dbc.NavLink("FAQ", href="faq"),
                        width="auto",
                        style={"color": "white"},
                        align="right",
                        className="mr-auto"
                        # width={"offset": 3},
                    ),
                ],align="center",
            ),
        ], color="dark", dark=True, fixed="top")


updatemenus = [
        dict(
            type="buttons",
            xanchor="right",
            yanchor="bottom",
            direction="left",
            x=0.1,
            y=1.1,
            buttons=list([
                dict(
                    args=[{'yaxis.type': 'linear'}],
                    label="Linear Scale",
                    method="relayout"
                ),
                dict(
                    args=[{'yaxis.type': 'log'}],
                    label="Log Scale",
                    method="relayout"
                )
            ])
        ),
    ]

footer2 = html.Footer(html.Div([
    "Dashboard made by Jolene Zheng and Shafika Olalekan Koiki | ",
    html.A(" GitHub", href="https://github.com/jolenezheng/COVIDDashboard/", target="_blank")
], className="footer"))

site_backbone = html.Div([
    dcc.Location(id='url', refresh=False),
    #===BPH-FIXME Temporarily hidden navbar to see errors
    #html.Div(navbar2),
    html.Div(id='page-content', className="page border"),
    footer2,
])

app.layout = site_backbone

canadian_dashboard = html.Div(
    children=[
        dbc.Row(
            [
                dbc.Col([ 
                    dbc.Row(dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Static Input"),
                                dbc.CardBody([
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            children=[
                                                html.Div(children="Region", className="dropdown-title"),
                                                dcc.Dropdown(
                                                    id='region-dropdown',
                                                    className='dropdown',
                                                    options=[{'label':name, 'value':name} for name in names],
                                                    value = "Ontario" #list(fnameDict.keys())[0]
                                                ),
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            children=[
                                                html.Div(children="Sub-Region", className="dropdown-title"),
                                                dcc.Dropdown(
                                                    id='subregion-dropdown',
                                                    className='dropdown',
                                                    value = 'Toronto'
                                                ),
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            children=[
                                                html.Div(
                                                    children="Date Range",
                                                    className="dropdown-title",
                                                    id = "placeholder"
                                                    ),
                                                dcc.DatePickerRange(
                                                    id="date-range",
                                                    min_date_allowed=df_mort.date_death_report.min().date(),
                                                    max_date_allowed=df_mort.date_death_report.max().date(),
                                                    initial_visible_month=df_mort.date_death_report.max().date(),
                                                    start_date=df_mort.date_death_report.min().date(), # "2020-03-13"
                                                    end_date=df_mort.date_death_report.max().date(), #"2021-03-31"
                                                ),
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            dbc.Button("Rerun", id='rerun-btn1', n_clicks=0,
                                                       color="dark", className="mr-1")
                                        ),
                                    ), className='input-space'),
                                ]),
                            ], color="dark", outline=True),
                    ), className="mb-4"),
                    dbc.Row(dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Prediction Input"),
                                dbc.CardBody([
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            children=[
                                                html.Div(
                                                    children="Face Mask Google Trends",
                                                    className="dropdown-title"
                                                    ),
                                                dcc.Slider(
                                                    id='facemask-slider',
                                                    min=0,
                                                    max=100,
                                                    step=1,
                                                    value=0,
                                                    marks={
                                                        0: '0%',
                                                        25: '25%',
                                                        50: '50%',
                                                        75: '75%',
                                                        100: '100%'
                                                    },
                                                ),
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            children=[
                                                html.Div(
                                                    children="Reduction in Workplace Social Mobility",
                                                    className="dropdown-title"
                                                    ),
                                                dcc.Slider(
                                                    id='mobility-slider',
                                                    min=0,
                                                    max=100,
                                                    step=1,
                                                    value=0,
                                                    marks={
                                                        0: '0% (normal activity)',
                                                        # 25: '25%',
                                                        50: '50%',
                                                        75: '75%',
                                                        100: '100% (total lockdown)'
                                                    },
                                                ),
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            children=[
                                                html.Div(
                                                    children="Percent Vaccinated Per Week",
                                                    className="dropdown-title"
                                                    ),
                                                dcc.Slider(
                                                    id='vaccine-slider',
                                                    min=0,
                                                    max=20,
                                                    step=1,
                                                    value=0,
                                                    marks={
                                                        0: '0%',
                                                        5: '5%',
                                                        10: '10%',
                                                        15: '15%',
                                                        20: '20%',

                                                    },
                                                ),
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            children=[
                                                html.Div(
                                                    children="Date to Start Forecast",
                                                    className="dropdown-title",
                                                    ),
                                                dcc.DatePickerSingle(
                                                    id="forecast-start-date",
                                                    min_date_allowed=df_mort.date_death_report.min().date(),
                                                    max_date_allowed= df_mort.date_death_report.max().date(), # df_mort.date_death_report.max().date(),
                                                    initial_visible_month=df_mort.date_death_report.max().date(),
                                                    date= "2020-05-01", #"2021-04-01", # df_mort.date_death_report.max().date(), # "2020-11-01"
                                                    # end_date=df_mort.date_death_report.max().date(), #"2021-03-31"
                                                ),
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            children=[
                                                html.Div(
                                                    children="Number of Days to Forecast",
                                                    className="dropdown-title"
                                                    ),
                                                dcc.Slider(
                                                    id='forecast-slider',
                                                    min=0,
                                                    max=12,
                                                    step=1,
                                                    value=12, # todo: change back to 3
                                                    marks={ 0: '0 mo', 2: '2 mo', 4: '4 mo',
                                                        6: '6 mo', 8: '8 mo', 10: '10 mo', 12: '1 yr'
                                                    },
                                                ),
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            dbc.Button("Rerun", id='rerun-btn2', n_clicks=0,
                                                       color="dark", className="mr-1")
                                        ),
                                    ), className='input-space'),
                                ]),
                            ], color="dark", outline=True),
                    ), className="mb-4"),
                ], xl=3, lg=3, md=12, sm=12, xs=12), # ,width=3,className="column"),
                dbc.Col(
                    html.Div([
                        dbc.Row([
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Estimated Total Population"),
                                        dbc.CardBody(
                                            [
                                                dbc.Spinner(html.H5(id="total-pop-card",className="card-title"), size="sm")
                                            ]
                                        ),
                                    ],
                                    color="danger",
                                    inverse=True
                                )
                            ),
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(html.A("Population Sparsity", href="/faq", target="_blank", style={"color": "white", "size":"14px"})),
                                        dbc.CardBody(
                                            [
                                                dbc.Spinner(html.H5(id="sparsity-card",className="card-title"), size="sm")
                                            ]
                                        ),
                                    ],
                                    color="warning",
                                    inverse=True
                                )
                            ),
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Fraction of Population > 80"),
                                        dbc.CardBody(
                                            [
                                                dbc.Spinner(html.H5(id="frac-pop-card",className="card-title"), size="sm")
                                            ]
                                        ),
                                    ],
                                    color="success",
                                    inverse=True
                                )
                            ),
                            dbc.Col(
                                dbc.Card(
                                    [
                                        # dbc.CardHeader("Population Weighted Population Density"),
                                        dbc.CardHeader(html.A("Population Weighted Population Density", href="/faq", target="_blank", style={"color": "white", "size":"14px"})),
                                        dbc.CardBody(
                                            [
                                                dbc.Spinner(html.H5(id="pwpd-card",className="card-title"), size="sm")
                                            ]
                                        ),
                                    ],
                                    color="primary",
                                    inverse=True
                                )
                            ),
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Average Number / House"),
                                        dbc.CardBody(
                                            [
                                                dbc.Spinner(html.H5(id="avg-house-card",className="card-title"), size="sm")
                                            ]
                                        ),
                                    ],
                                    color="dark",
                                    inverse=True
                                )
                            ),
                        ], className="mb-4"),
                        dbc.Row([
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Covid Deaths / Total Population"),
                                        dbc.CardBody(
                                            [
                                                dbc.Spinner(html.H5(id="covid-deaths-card",className="card-title"), size="sm")
                                            ]
                                        ),
                                    ],
                                    color="danger",
                                    inverse=True
                                )
                            ),
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Cases / Total Population"),
                                        dbc.CardBody(
                                            [
                                                dbc.Spinner(html.H5(id="cases-card",className="card-title"), size="sm")
                                            ]
                                        ),
                                    ],
                                    color="warning",
                                    inverse=True
                                )
                            ),
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Covid Deaths / Annual Deaths"),
                                        dbc.CardBody(
                                            [
                                                dbc.Spinner(html.H5(id="covid-deaths2-card",className="card-title"), size="sm")
                                            ]
                                        ),
                                    ],
                                    color="success",
                                    inverse=True
                                )
                            ),
                            dbc.Col(
                                dbc.Card(
                                    [
                                        # dbc.CardHeader("Population Weighted Population Density"),
                                        dbc.CardHeader("7-day Average Workplace Mobility"),
                                        dbc.CardBody(
                                            [
                                                dbc.Spinner(html.H5(id="mob-card",className="card-title"), size="sm")
                                            ]
                                        ),
                                    ],
                                    color="primary",
                                    inverse=True
                                )
                            ),
                        ], className="mb-4"),
                        dbc.Row(dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardHeader(id="cases-header"),
                                    dbc.CardBody(
                                         dcc.Loading(
                                            children=[html.Div(dcc.Graph(
                                                id="cases-chart", config={"displayModeBar": False}))],
                                            type="default"
                                    )),
                                ], color="dark", inverse=True),
                        ), className="mb-4"),
                        dbc.Row(dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardHeader(id="simulation-header"),
                                    dbc.CardBody(
                                         dcc.Loading(
                                            children=[html.Div(dcc.Graph(
                                                id="simulation-chart", config={"displayModeBar": False}))],
                                            type="default"
                                    )),
                                    # dbc.CardBody(
                                    #     dcc.Graph(
                                    #         id="cases-chart", config={"displayModeBar": False}, # style={'display': 'inline-block'},
                                    #     ),
                                    # ),
                                ], color="dark", inverse=True),
                        ), className="mb-4"),
                        dbc.Row(
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(id="cumulativedeaths-header"),
                                        dbc.CardBody(
                                            dcc.Loading(
                                                children=[html.Div(dcc.Graph(
                                                    id="cumulativedeaths-chart", config={"displayModeBar": False}))],
                                                type="default"
                                            )),
                                        # dbc.CardBody(
                                        #     dcc.Graph(
                                        #         id="cases-chart", config={"displayModeBar": False}, # style={'display': 'inline-block'},
                                        #     ),
                                        # ),
                                    ], color="dark", inverse=True),
                            ), className="mb-4"),                        
                        dbc.Row([
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(id="mob-header"),
                                        dbc.CardBody(
                                            dcc.Loading(
                                                children=[html.Div(dcc.Graph(
                                                    id="mobility-chart", config={"displayModeBar": False}))],
                                                type="default"
                                        )),
                                        # dbc.CardBody(
                                        #     dcc.Graph(
                                        #         id="mobility-chart", config={"displayModeBar": False}, # style={'display': 'inline-block'},
                                        #     ),
                                        # ),
                                    ], color="dark", inverse=True),
                            ),
                        ], className="mb-4"),
                        dbc.Row([                        
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(id="vac-header"),
                                        dbc.CardBody(
                                            dcc.Loading(
                                                children=[html.Div(dcc.Graph(
                                                    id="vac-chart", config={"displayModeBar": False}))],
                                                type="default"
                                        )),
                                        # dbc.CardBody(
                                        #     dcc.Graph(
                                        #         id="vac-chart", config={"displayModeBar": False}, # style={'display': 'inline-block'},
                                        #     ),
                                        # ),
                                    ], color="dark", inverse=True),
                            ), 
                        ], className="mb-4"),
                        dbc.Row([
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(id="temp-header"),
                                        dbc.CardBody(
                                            dcc.Loading(
                                                children=[html.Div(dcc.Graph(
                                                    id="weather-chart", config={"displayModeBar": False}))],
                                                type="default"
                                        )),
                                        # dbc.CardBody(
                                        #     dcc.Graph(
                                        #         id="weather-chart", config={"displayModeBar": False}, # style={'display': 'inline-block'},
                                        #     ),
                                        # ),
                                    ], color="dark", inverse=True),
                            ),
                        ], className="mb-4"),                            
                        dbc.Row([                            
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(id="trends-header"),
                                        dbc.CardBody(
                                            dcc.Loading(
                                                children=[html.Div(dcc.Graph(
                                                    id="trends-chart", config={"displayModeBar": False}))],
                                                type="default"
                                        )),
                                        # dbc.CardBody(
                                        #     dcc.Graph(
                                        #         id="trends-chart", config={"displayModeBar": False}, # style={'display': 'inline-block'},
                                        #     ),
                                        # ),
                                    ], color="dark", inverse=True),
                            ),
                        ], className="mb-4"),
                        dbc.Row([	
                            dbc.Col(	
                                dbc.Card(	
                                    [	
                                        dbc.CardHeader(id="rtcurve-header"),
                                        dbc.CardBody(
                                            dcc.Loading(
                                                children=[html.Div(dcc.Graph(
                                                    id="rtcurve-chart", config={"displayModeBar": False}))],
                                                type="default"
                                        )),
                                    ], color="dark", inverse=True),	
                            ),	
                        ], className="mb-4"),
                        # dbc.Row([	
                        #     dbc.Col(	
                        #         dbc.Card(	
                        #             [	
                        #                 dbc.CardHeader("7-day Average Facemask"), #(id="trends-calibration-header"),
                        #                 dbc.CardBody(
                        #                     dcc.Loading(
                        #                         children=[html.Div(dcc.Graph(
                        #                             id="trends-calibration-chart", config={"displayModeBar": False}))],
                        #                         type="default"
                        #                 )),
                        #             ], color="dark", inverse=True),	
                        #     ),	
                        # ], className="mb-4"),
                    ]),
                    className="column",
                    xl=9, lg=9, md=12, sm=12, xs=12,
                ),
            ], className="mb-4"
        ),
    ],
)

# function to return current timestamp
def nowtime():
    return datetime.datetime.now().time()

@app.callback(
    ddp.Output('page-content', 'children'),
    [ddp.Input('url', 'pathname')]
)
def display_page(pathname):
    if (pathname == "/"):
        return canadian_dashboard
    elif (pathname == "/about"):
        return about_page
    elif (pathname == "/faq"):
        return faq_page2
    elif (pathname == "/intro"):
        return introduction_page
    
    print("START-END --- display_page \t", nowtime())
    return canadian_dashboard

# FAQ Page
@app.callback(
    [
        ddp.Output("a1", "is_open"), ddp.Output("a2", "is_open"), ddp.Output("a3", "is_open"), ddp.Output("a4", "is_open"),
        ddp.Output("a5", "is_open"), ddp.Output("a6", "is_open"), ddp.Output("a7", "is_open"), ddp.Output("a8", "is_open"),
        ddp.Output("a9", "is_open"), ddp.Output("a10", "is_open"), ddp.Output("a11", "is_open"), ddp.Output("a12", "is_open"),
        ddp.Output("a13", "is_open"), ddp.Output("a14", "is_open"), ddp.Output("a15", "is_open")
    ],
    [
        ddp.Input("q1", "n_clicks"), ddp.Input("q2", "n_clicks"), ddp.Input("q3", "n_clicks"), ddp.Input("q4", "n_clicks"),
        ddp.Input("q5", "n_clicks"), ddp.Input("q6", "n_clicks"), ddp.Input("q7", "n_clicks"), ddp.Input("q8", "n_clicks"),
        ddp.Input("q9", "n_clicks"), ddp.Input("q10", "n_clicks"), ddp.Input("q11", "n_clicks"), ddp.Input("q12", "n_clicks"),
        ddp.Input("q13", "n_clicks"), ddp.Input("q14", "n_clicks"), ddp.Input("q15", "n_clicks")
    ],
    [
        ddp.State("a1", "is_open"), ddp.State("a2", "is_open"), ddp.State("a3", "is_open"), ddp.State("a4", "is_open"),
        ddp.State("a5", "is_open"), ddp.State("a6", "is_open"), ddp.State("a7", "is_open"), ddp.State("a8", "is_open"),
        ddp.State("a9", "is_open"), ddp.State("a10", "is_open"), ddp.State("a11", "is_open"), ddp.State("a12", "is_open"),
        ddp.State("a13", "is_open"), ddp.State("a14", "is_open"), ddp.State("a15", "is_open")
    ],
)
def toggle_collapse(q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14, q15, is_open1, is_open2, is_open3, is_open4, is_open5, is_open6, is_open7, is_open8, is_open9, is_open10, is_open11, is_open12, is_open13, is_open14, is_open15):
    questions = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14, q15]
    states = [is_open1, is_open2, is_open3, is_open4, is_open5, is_open6, is_open7, is_open8, is_open9, is_open10, is_open11, is_open12, is_open13, is_open14, is_open15]
    #===BPH-FIXME Should not have global variables here
    #             Not fixing it now because it's not a vital element.
    global prev_states

    for i in range(15):
        q = questions[i]
        if q and q != prev_states[i]:
            states[i] = not states[i]
            prev_states[i] = questions[i]

    print("START-END --- toggle_collapse \t", nowtime())
        
    return states


@app.callback(
    [
        ddp.Output("facemask-slider", "value"),
        ddp.Output("mobility-slider", "value"),
        ddp.Output("vaccine-slider", "value"),
        ddp.Output("forecast-slider", "value"),
    ],
    [
        #===BPH Changed all but sub-region to State
        #       Only activates on change of sub-region.
        ddp.Input('subregion-dropdown', 'value')
    ],
    [  
        ddp.State('region-dropdown', 'value'), 
        ddp.State("forecast-start-date", "date"),
    ]
)
def init_slider_vals(region_name, province_name, date_str):

    print("START --- init_slider_vals \t\t", nowtime())
    
    #===BPH Should not be changing a global variable. If df_mobility
    #       is being used for sharing data between callbacks, then 
    #       something else could be tried, see:
    #
    #           https://dash.plotly.com/sharing-data-between-callbacks
    #
    #       At this point, I halt use of global df_mobility and
    #       just have the function get_mob return a local variable.
    #
    #global df_mobility

    #===BPH this was missing:
    province_name = update_province_name(province_name)

    df_mobility = get_mob(province_name, region_name)
    date = datetime.datetime.strptime(date_str, '%Y-%m-%d')

    #===BPH Should not have a global variable here.
    #       For now, just use *only* the initial_load behavior
    #global initial_load

    #===BPH-FIXME I think the sliders should be set to current
    #             values independent of when the forecast begins.
    #             I can't tell if that is happening here
    initial_load = False

    # vac_dates = get_vaccination_dates(province_name, region_name)
    df_vac = vaccination_data(province_name, region_name)
    last_vac = get_last_vac(province_name, region_name)

    #===BPH-FIXME This name should really be changed to *months*
    num_days_to_forecast = 12

    if (initial_load):
        #===BPH pass the local df_mobility variable
        mob = get_last_mob(df_mobility)
        trends = get_last_trends(province_name, region_name)
        vac = last_vac / round(get_total_pop(province_name, region_name), 0) * 100
    else:
        #===BPH pass the local df_mobility variable
        mob = -get_mob_on_day(df_mobility, date, 0, 0)
        # trends = get_last_trends(province_name, region_name)
        trends = get_trends_on_day(province_name, region_name, date, 0)
        total_pop = get_total_pop(province_name, region_name)
        vac = get_vac_on_day(date, 0, total_pop, df_vac, 0, False, last_vac)

    print("END   --- init_slider_vals \t\t", nowtime())
    
    #initial_load = False
    return trends, mob, 3, num_days_to_forecast # todo: change 0 -> vac

@app.callback(
    [
        ddp.Output('total-pop-card', 'children'),
        ddp.Output('sparsity-card', 'children'),
        ddp.Output('frac-pop-card', 'children'),
        ddp.Output('pwpd-card', 'children'),
        ddp.Output('avg-house-card', 'children'),
        ddp.Output('mob-card', 'children'),
        ddp.Output("simulation-header", "children"),
        ddp.Output("cases-header", "children"),
        ddp.Output("mob-header", "children"),
        ddp.Output("temp-header", "children"),
        ddp.Output("vac-header", "children"),
        ddp.Output("trends-header", "children"),
        ddp.Output("rtcurve-header", "children"),
        ddp.Output("cumulativedeaths-header", "children")
    ],
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks')
    ],
    [
        ddp.State('region-dropdown', 'value'),
        ddp.State('subregion-dropdown', 'value')
    ]
)
def update_region_names(n_clicks1, n_clicks2, province_name, region_name):

    print("START --- update_region_names \t\t", nowtime())
    
    province_name = update_province_name(province_name)
    
    # need df_mobility for get_last_mob() below
    df_mobility = get_mob(province_name, region_name)
    # Card Values
    total_pop = round(get_total_pop(province_name, region_name), 0)
    sparsity = round(get_pop_sparsity(province_name, region_name), 3)
    pop_80 = round(get_frac_pop_over_80(province_name, region_name), 3)
    pwpd = round(get_pwpd(province_name, region_name), 0)
    mob = str(0 - get_last_mob(df_mobility)) + "%"

    # todo: sparsity (3 digits)
    # pop_80 = round(get_frac_pop_over_80(province_name, region_name), 2)
    # pwpd = round(get_pwpd(province_name, region_name), 2)
    avg_house = round(get_avg_house(province_name, region_name), 2)
    # Graph Titles
    deaths_label = 'Daily Predicted Deaths in ' + region_name + ', ' + province_name \
        + " (black = actual)"
    cases_label = 'Daily Reported Cases in ' + region_name + ', ' + province_name
    mob_label = 'Workplace Social Mobility in ' + region_name + ', ' + province_name
    temp_label = 'Daily Reported Temperature in ' + region_name + ', ' + province_name
    vac_label = 'Fraction of the Population Vaccinated in ' + region_name + ', ' + province_name
    trends_label = 'Google Searches for Face Masks in ' + region_name + ', ' + province_name
    rtcurve_label = 'Effective Reproduction Number R(t) Curves in ' + region_name + ', ' \
        + province_name + " (black = actual, colors = predicted)"
    cumulativedeaths_label = 'Cumulative Deaths in ' + region_name + ', ' + province_name

    print("END   --- update_region_names \t\t", nowtime())
    
    return total_pop, sparsity, pop_80, pwpd, avg_house, mob, deaths_label, cases_label, mob_label, temp_label, vac_label, trends_label, rtcurve_label, cumulativedeaths_label

@app.callback(
    [
        ddp.Output('covid-deaths-card', 'children'),
        ddp.Output('cases-card', 'children'),
        ddp.Output('covid-deaths2-card', 'children'),
    ],
    [
        #===BPH Only re-run button triggers
        ddp.Input('rerun-btn1', 'n_clicks'),        
        ddp.Input('rerun-btn2', 'n_clicks')        
    ],
    [
        ddp.State('region-dropdown', 'value'),
        ddp.State('subregion-dropdown', 'value'),
        ddp.State("date-range", "start_date"),
        ddp.State("date-range", "end_date"),
    ]
)
def update_dynamic_cards(n_clicks1, n_clicks2, province_name, region_name, start_date, end_date):

    print("START --- update_dynamic_cards \t\t", nowtime())

    #===BPH this was missing:
    province_name = update_province_name(province_name)
    
    total_covid_deaths = get_total_deaths(province_name, region_name, start_date, end_date, False)
    total_population = get_total_pop(province_name, region_name)

    year = end_date.split("-")[0]
    start_date_this_year = year + "-01-01"
    annual_deaths = get_ann_death(province_name, region_name)
    annual_covid_deaths = get_total_deaths(province_name, region_name, start_date_this_year, end_date, False)

    deaths_ann = str(round(annual_covid_deaths / annual_deaths * 100.0, 3)) + "%"
    deaths_per_pop = str(round(total_covid_deaths / total_population * 100.0, 3)) + "%"

    total_cases = get_total_cases(province_name, region_name, start_date, end_date)
    cases_per_pop = str(round(total_cases / total_population * 100.0, 3)) + "%"

    print("END   --- update_dynamic_cards \t\t", nowtime())

    return deaths_per_pop, cases_per_pop, deaths_ann

@app.callback(
    ddp.Output('subregion-dropdown', 'options'),
    ddp.Input('region-dropdown', 'value')
)
def update_subregion_dropdown(name):
    #===BPH re-named this function from "update_date_dropdown"
    print("START --- update_subregion_dropdown \t", nowtime())
    print("END   --- update_subregion_dropdown \t", nowtime())    
    return [{'label': i, 'value': i} for i in fnameDict[name]]


 # ============== SLIDER CALLBACK ==============


# Update names to abbreviated form
def update_province_name(province_name):
    if (province_name == "Newfoundland and Labrador"):
        province_name = "NL"
    elif (province_name == "British Columbia"):
        province_name = "BC"
    elif (province_name == "Prince Edward Island"):
        province_name == "PEI"
    elif (province_name == "Northwest Territories"):
        province_name == "NWT"

    return province_name

@app.callback(
    ddp.Output("simulation-chart", "figure"),
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks')        
    ],
    [
        #===BPH Changed all to State from Input
        #       Also added rerun-btn as Input
        ddp.State("region-dropdown", "value"),
        ddp.State("subregion-dropdown", "value"),
        ddp.State("date-range", "start_date"),
        ddp.State("date-range", "end_date"),
        ddp.State("forecast-start-date", "date"),
        ddp.State('forecast-slider', 'value'),
        ddp.State('facemask-slider', 'value'),
        ddp.State('mobility-slider', 'value'),
        ddp.State('vaccine-slider', 'value'),
    ],
)
def update_mortality_chart(n_clicks1, n_clicks2, province_name, region, start_date, end_date,
                           day_to_start_forecast, days_to_forecast, facemask, xMob, vac):    
    #===BPH-FIXME forbid predictions prior to March 2020
    
    print("START --- update_mortality_chart \t", nowtime())
    
    province_name = update_province_name(province_name)
    xMob = -xMob
    facemask = facemask * 70 / 100
    vac = vac / 100.0
    today = datetime.datetime.now()
    death_dates = date(province_name, region, start_date, today.strftime("%Y-%m-%d"))
    death_vals = r_avg(province_name, region, start_date, end_date)
    
    df_mobility = get_mob(province_name, region)
    pred_fig = go.Figure()

    df_vac = vaccination_data(province_name, region)

    print("      --- update_mortality_chart \t", nowtime(), " --- started getting weather")
    #===BPH Get weather dataframe
    df_weather = get_weather_dataframe(province_name, region)
    print("      --- update_mortality_chart \t", nowtime(), " --- finished getting weather")    
    
    # fig.update_xaxes(type="log", range=[0,5])
    time.sleep(2)
    for i in range(number_of_simulations):
        if (i < 2):
            time.sleep(3)

        print("      --- update_mortality_chart \t", nowtime(), " --- D(t) CURVE: " + str(i))
        #print("===== DEATH CURVE: " + str(i) + " ========")
        dates = predicted_dates(province_name, region, start_date, day_to_start_forecast, days_to_forecast)
        deaths = predicted_deaths(i, province_name, region, start_date, day_to_start_forecast, days_to_forecast, df_mobility, xMob, facemask, vac, df_vac, df_weather)[0]
        # if (i > 1):
        pred_fig.add_trace(go.Scatter(
            x=dates,
            y=deaths,
            name='Prediction ' + str(i+1),
        ))

    pred_fig.add_trace(go.Scatter(
        x=death_dates, # here
        y=death_vals, # here
        name='Previous Deaths',
        line=dict(color='black', width=2),
    ))

    pred_fig.update_layout(xaxis_title='Date',
                   yaxis_title='Daily Mortality (7-day Rolling Avg)',
                   showlegend=False,                           
                   updatemenus=updatemenus)

    print("END   --- update_mortality_chart \t", nowtime())
    
    return pred_fig

@app.callback(
    ddp.Output("cases-chart", "figure"), # ddp.Output("map1", "figure"), ddp.Output("map2", "figure")],
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks')                
    ],
    [
        #===BPH Changed all to State from Input
        #       Added rerun-btn Input
        ddp.State("region-dropdown", "value"),
        ddp.State("subregion-dropdown", "value"),
        ddp.State("date-range", "start_date"),
        ddp.State("date-range", "end_date"),
    ],
)
def update_cases_charts(n_clicks1, n_clicks2, province_name, region, start_date, end_date):
    print("START --- update_cases_chart \t\t", nowtime())
    
    province_name = update_province_name(province_name)
    # xMob = -xMob
    # facemask = facemask * 70 / 100
    # vac = vac / 100.0
    today = datetime.datetime.now()
    cases_dates = date(province_name, region, start_date, today.strftime("%Y-%m-%d"))
    cases_vals = ravg_cases(province_name, region, start_date, today.strftime("%Y-%m-%d"))

    #===BPH remove global df_mobility variable    
    #global df_mobility
    df_mobility = get_mob(province_name, region)
    # set_last_mob()

    cases_fig = go.Figure()
    
    # for i in range(5):
    #     cases_fig.add_trace(go.Scatter(
    #         x=predicted_dates(province_name, region, start_date, day_to_start_forecast, days_to_forecast),
    #         y=predicted_cases(province_name, region, start_date, day_to_start_forecast, days_to_forecast, df_mobility, xMob, facemask, vac),
    #         name='Predicted Cases',
    #     ))

    cases_fig.add_trace(go.Scatter(
        x=cases_dates,
        y=cases_vals,
        name='Previous Cases',
        line=dict(color='black', width=2),
    ))

    cases_fig.update_layout(xaxis_title='Date',
                   yaxis_title='Daily Cases (7-day Rolling Avg)',
                   updatemenus=updatemenus)

    print("END   --- update_cases_chart \t\t", nowtime())    

    return cases_fig

@app.callback(
    ddp.Output("weather-chart", "figure"),
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks')        
    ],
    [
        #===BPH Changed all to State from Input
        #       Added rerun-btn as Input
        ddp.State("region-dropdown", "value"),
        ddp.State("subregion-dropdown", "value"),
        ddp.State("date-range", "start_date"),
        ddp.State("date-range", "end_date"),
        ddp.State('forecast-slider', 'value'),
    ],
)
def update_weather_chart(n_clicks1, n_clicks2, province_name, region, start_date, end_date,
                         forecasted_dates,):
    print("START --- update_weather_chart \t\t", nowtime())

    province_name = update_province_name(province_name)

    #===BPH Get weather dataframe
    df_weather = get_weather_dataframe(province_name, region)
    # select out current and future data
    today = datetime.datetime.today()
    df_weather = df_weather[df_weather.date.between(start_date, end_date)]
    df_weather_current = df_weather[df_weather.date < today]
    df_weather_future = df_weather[df_weather.date >= today]    

    weather_fig = px.line(df_weather_current, x = 'date', y = 'temp_mean')
    
    weather_fig.update_layout(xaxis_title='Date',	
                   yaxis_title='Mean Temperature',
                   showlegend=False,)	

    weather_fig.add_trace(go.Scatter(	
        x = df_weather_future['date'],
        y = df_weather_future['temp_mean'],
        mode = 'lines',
        name='Historical Average',	
        ))
    
    print("END   --- update_weather_chart \t\t", nowtime())
    
    return weather_fig

@app.callback(
    ddp.Output("mobility-chart", "figure"),
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks')         
    ],        
    [
        #===BPH Changed all to State from Input
        #       Added rerun-btn as Input
        ddp.State("region-dropdown", "value"),
        ddp.State("subregion-dropdown", "value"),
        ddp.State("date-range", "start_date"),
        ddp.State("date-range", "end_date"),
        ddp.State('forecast-slider', 'value'),
        ddp.State('mobility-slider', 'value'),
    ],
    #===BPH-FIXME Picking up wrong values on initial call, so prevent
    # prevent_initial_call=True
)
def update_mob_charts(n_clicks1, n_clicks2, province_name, region, start_date, end_date,
                      forecasted_dates, xMob):
    print("START --- update_mob_charts \t\t", nowtime())
    print("      --- update_mob_charts \t\t", nowtime(), " --- xMob=" + str(xMob))

    
    province_name = update_province_name(province_name)
    xMob = -xMob
    dates = predicted_dates(province_name, region, start_date, end_date, forecasted_dates)
    mob_values = []
    for i in range(len(dates)):
        mob_values.append(xMob)
    
     # ============== MOBILITY GRAPH ==============
    mobility_fig = px.line(df_mort, x = date_mob(province_name, region, start_date, end_date), y = mobility(province_name, region, start_date, end_date))
    mobility_fig.update_layout(xaxis_title='Date',
                   yaxis_title='Workplace Social Mobility',
                   showlegend=False,)
    mobility_fig.add_trace(go.Scatter(
            x=dates,
            y=mob_values,
            name='Simulated Mobility',
        ))
    
    print("END   --- update_mob_charts \t\t", nowtime())
    
    return mobility_fig

@app.callback(
    ddp.Output("vac-chart", "figure"),
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks')         
    ],
    [
        #===BPH Changed all to State from Input
        #       Added rerun-btn as Input
        ddp.State("region-dropdown", "value"),
        ddp.State("subregion-dropdown", "value"),
        ddp.State("date-range", "start_date"),
        ddp.State("date-range", "end_date"),
        ddp.State('forecast-slider', 'value'),
        ddp.State('vaccine-slider', 'value'),
    ],
    #===BPH-FIXME Picking up wrong values on initial call, so prevent
    # prevent_initial_call=True
)
def update_vaccination_charts(n_clicks1, n_clicks2, province_name, region, start_date, end_date,
                              forecasted_dates, vac_slider_val):
    print("START --- update_vaccination_chart \t", nowtime())
    
    #===BPH This commented-stuff will no longer work because the
    #       global variable df_vac2 was removed.
    # while (df_vac2.empty):
    #     time.sleep(1)
    #     print("SLEEPING!!!!!")

    # if (not df_vac2.empty):
    #     print(df_vac2)
    # print("df_vac2.empty: " + str(df_vac2.empty))
    province_name = update_province_name(province_name)
    df_vac = vaccination_data(province_name, region)
    regional_population = get_total_pop(province_name, region)
    provincial_population = get_prov_pop(province_name, region)
    total_pop = get_total_pop(province_name, region)
    last_vac = get_last_vac(province_name, region)
    vac_slider_val = vac_slider_val / 100.0
    dates = predicted_dates(province_name, region, start_date, end_date, forecasted_dates)
    vac_forecasted_values = []
    for i in range(len(dates)):
        date_in_forecast = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=i)
        printpls = False
        curr_vac = get_vac_on_day(date_in_forecast, vac_slider_val, total_pop, df_vac, 0, printpls, last_vac)
        vac_forecasted_values.append(curr_vac)

    vac_dates = []
    vac_vals = []

    for day in df_vac:
        if (day["total_vaccinations"] != None):
            date = day['date']
            vac_dates.append(date)
            if (province_name == 'Alberta') or (province_name == 'New Brunswick') or (province_name == 'NL') or (province_name == 'Nova Scotia'):
                vaccine = day['total_vaccinations'] / provincial_population
            else:
                vaccine = day['total_vaccinations'] / regional_population
            
            vac_vals.append(vaccine)
        

    vaccination_fig = px.line(vac_vals, x = vac_dates, y = vac_vals)
    vaccination_fig.update_layout(xaxis_title='Date',
                   yaxis_title='Total Vaccinations/Population of Region', showlegend=False)
    vaccination_fig.add_trace(go.Scatter(
            x=dates,
            y=vac_forecasted_values,
            name='Simulated Vaccinations',
        ))

    print("END   --- update_vaccination_chart \t", nowtime())
    
    return vaccination_fig

@app.callback(
    ddp.Output("trends-chart", "figure"), # ddp.Output("trends-calibration-chart", "figure") ],
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks')        
    ],
    [
        #===BPH Changed all to State from Input
        #       Added rerun-btn as a Input
        ddp.State("region-dropdown", "value"),
        ddp.State("subregion-dropdown", "value"),
        ddp.State("date-range", "start_date"),
        ddp.State("date-range", "end_date"),
        ddp.State('forecast-slider', 'value'),
        ddp.State('facemask-slider', 'value'),
    ],
    #===BPH-FIXME Picking up wrong values on initial call, so prevent
    # prevent_initial_call=True    
)
def update_trends_charts(n_clicks1, n_clicks2, province_name, region, start_date, end_date,
                         forecasted_dates, mask_slider_val):
    print("START --- update_trends_chart \t\t", nowtime())
    
    province_name = update_province_name(province_name)

    dates = predicted_dates(province_name, region, start_date, end_date, forecasted_dates)
    trends_vals = []
    for i in range(len(dates)):
        trends_vals.append(mask_slider_val)

    df_trends = df_trends_data(province_name, region)
    trends_past_dates = df_trends['date']
    trends_past_vals = df_trends[str(get_geocode(province_name, region))]
    trends_fig = px.line(df_trends, x = trends_past_dates, y = trends_past_vals)
    trends_fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Number of Google Searches for Face Masks',
        showlegend=False,
    )
    trends_fig.add_trace(go.Scatter(
            x=dates,
            y=trends_vals,
            name='Simulated Facemask Use',
        ))

    first_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    mid_april = datetime.datetime.strptime("2021-04-15", "%Y-%m-%d").date()
    
    days_since_first_day = first_date - mid_april
    delta = days_since_first_day.days

    #print("FIRST DATE: " + str(first_date))
    #print("mid_april: " + str(mid_april))
    #print("delta: " + str(delta))

    facemask_vals = []
    for i in range(len(trends_past_vals)):
        gTrends = trends_past_vals[i]
        fm = gTrends * 0.5 * (1 + (np.tanh(delta) / 14))
        facemask_vals.append(fm)

    facemask_fig = px.line(df_trends, x = trends_past_dates, y = facemask_vals)
    facemask_fig.update_layout(xaxis_title='Date',
                   yaxis_title='7-day Average Facemask')

    print("END   --- update_trends_chart \t\t", nowtime())

    return trends_fig #, facemask_fig

@app.callback(
    ddp.Output("rtcurve-chart", "figure"),
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks')        
    ],
    [
        #===BPH Changed all to State from Input
        #       Added rerun-btn as Input
        ddp.State("region-dropdown", "value"),
        ddp.State("subregion-dropdown", "value"),
        ddp.State("date-range", "start_date"),
        ddp.State("date-range", "end_date"),
        ddp.State("forecast-start-date", "date"),
        ddp.State('forecast-slider', 'value'),
        ddp.State('facemask-slider', 'value'),
        ddp.State('mobility-slider', 'value'),
        ddp.State('vaccine-slider', 'value'),   
    ],
)
def update_rtcurve_charts(n_clicks1, n_clicks2, province_name, region, start_date, end_date,
                          day_to_start_forecast, days_to_forecast, facemask, xMob, vac):
    print("START --- update_rtcurve_charts \t", nowtime())
    
    province_name = update_province_name(province_name)
    xMob = -xMob
    facemask = facemask * 70 / 100
    vac = vac / 100.0
    
    df_mobility = get_mob(province_name, region)    
    
    df_vac = vaccination_data(province_name, region)
    
    print("      --- update_rtcurve_charts \t", nowtime(), " --- started getting weather")
    #===BPH Get weather dataframe
    df_weather = get_weather_dataframe(province_name, region)
    print("      --- update_rtcurve_charts \t", nowtime(), " --- finished getting weather")
    
    rtcurve_fig = go.Figure()
    
    # ============== R(T) CURVE GRAPH ==============
    for i in range(number_of_simulations):
        print("      --- update_rtcurve_charts \t", nowtime(), " --- R(t) CURVE: " + str(i))
        #print("===== R(t) CURVE: " + str(i) + " ========")
        
        rtcurve_fig.add_trace(go.Scatter(
            x=predicted_dates(province_name, region, start_date, day_to_start_forecast, days_to_forecast),
            y=predicted_deaths(0, province_name, region, start_date, day_to_start_forecast, days_to_forecast, df_mobility, xMob, facemask, vac, df_vac, df_weather)[1],
        name = 'R(t)'
    ))

    rtcurve_fig.add_trace(go.Scatter(
            x=date(province_name, region, start_date, end_date),
            y=past_rt_equation(province_name, region),
            name='Previous R(t)',
            line=dict(color='black', width=2),
    ))

    updatemenus = [
        dict(
            type="buttons",
            xanchor="right",
            yanchor="bottom",
            direction="left",
            x=0.1,
            y=1.1,
            buttons=list([
                dict(
                    args=[{'yaxis.type': 'linear'}],
                    label="Linear Scale",
                    method="relayout"
                ),
                dict(
                    args=[{'yaxis.type': 'log'}],
                    label="Log Scale",
                    method="relayout"
                )
            ])
        ),
    ]    

    rtcurve_fig.update_layout(xaxis_title='Date',
                   yaxis_title='R(t) Curve Based On Mortality',
                   updatemenus=updatemenus)

    print("END   --- update_rtcurve_charts \t", nowtime())

    return rtcurve_fig

@app.callback(
    ddp.Output("cumulativedeaths-chart", "figure"),
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks')
    ],
    [
        ddp.State("region-dropdown", "value"),
        ddp.State("subregion-dropdown", "value"),
        ddp.State("date-range", "start_date"),
        ddp.State("date-range", "end_date"),
    ],
)
def update_cumulativedeaths_charts(n_clicks1, n_clicks2, province_name, region,
                                   start_date, end_date):
    print("START --- update_cumulativedeath_chart \t", nowtime())
    
    province_name = update_province_name(province_name)
    dates = date(province_name, region, start_date, end_date)
    cumulativedeaths = cumulative_deaths(province_name, region, start_date, end_date)
    
    cumulativedeaths_fig = go.Figure()
    
     # ============== MOBILITY GRAPH ==============
    cumulativedeaths_fig.add_trace(go.Scatter(
            x=dates,
            y=cumulativedeaths,
            name='Cumulative Deaths',
        ))
    
    cumulativedeaths_fig.update_layout(xaxis_title='Date',
                   yaxis_title='Number of Deaths')
    print("START --- update_cumulativedeath_chart \t", nowtime())
    
    return cumulativedeaths_fig


# -------------- STATIC DATA HELPER FUNCTIONS --------------

def get_region_info(province_name, region_name):
    prov_info = static_data[static_data.province_name == province_name]
    region_info = prov_info[prov_info.health_region == region_name]
    return region_info

def get_avg_house(province_name, region_name):
    return get_region_info(province_name, region_name).house.item()

def get_land_area(province_name, region_name):
    return get_region_info(province_name, region_name).landarea.item()

def get_total_pop(province_name, region_name):
    return get_region_info(province_name, region_name).total_pop.item()

def get_prov_pop(province_name, region_name):
    return get_region_info(province_name, region_name).prov_pop.item()

def get_ann_death(province_name, region_name):
    return get_region_info(province_name, region_name).anndeath.item()

def get_frac_pop_over_80(province_name, region_name):
    frac_over_80 = get_region_info(province_name, region_name).pop80.item()
    return frac_over_80 / get_total_pop(province_name, region_name)

def get_pwpd(province_name, region_name):
    return get_region_info(province_name, region_name).pwpd.item()

def get_pop_sparsity(province_name, region_name):	
    return get_region_info(province_name, region_name).pop_sparsity.item()

def climateid(province_name, region_name):
    # Gets the climate ID for the health region
    weat_info_province = static_data[static_data.province_name == province_name]
    return weat_info_province.climate_id[weat_info_province.health_region == region_name].item()

def get_provinceid(province_name, region_name):
    # Gets the province abbreviation for the health region
    weat_info_province = static_data[static_data.province_name == province_name]
    return weat_info_province.prov_id[weat_info_province.health_region == region_name].item()

def get_hruid(province_name, region_name):
    # Gets the hr_uid for the health region
    weat_info_province = static_data[static_data.province_name == province_name]
    return weat_info_province.hr_uid[weat_info_province.health_region == region_name].item()

# -------------- PREDICTIVE MODEL HELPER FUNCTIONS --------------

def predicted_dates(province_name, region_name, start_date, end_date, days_to_forecast):
    base = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    add_dates = [base + datetime.timedelta(days=x) for x in range(days_to_forecast * 30)]

    for i in range(len(add_dates)):
        add_dates[i] = datetime.datetime.strptime(str(add_dates[i]), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
    
    return add_dates

def predicted_deaths(c_num, province_name, region_name, start_date, end_date, days_to_forecast, df_mobility, xMob_slider, facemask_val, vac_val, df_vac, df_weather):
    base = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    add_dates = [base + datetime.timedelta(days=x) for x in range(days_to_forecast * 30)]
    yVals = []
    lambda_values = [] 

    yes_print2 = False
    #if (c_num == 4):
    #    yes_print2 = True
    total_deaths = get_total_deaths(province_name, region_name, start_date, end_date, yes_print2)
    last_mort = get_last_mort(province_name, region_name, start_date, end_date)
    last_vac = get_last_vac(province_name, region_name)

    total_population = get_total_pop(province_name, region_name)
    annDeath = get_ann_death(province_name, region_name)
    
    xHouse = get_avg_house(province_name, region_name) # Average number of people/household
    xLogPWPD = math.log(get_pwpd(province_name, region_name) * get_frac_pop_over_80(province_name, region_name), 10)
    xBeta = math.log(total_population / (get_pwpd(province_name, region_name) * get_land_area(province_name, region_name))) / math.log(0.25**2/get_land_area(province_name, region_name))
    first = True
    deaths_tomorrow = 0.0
    deaths_today = last_mort
    [total_deaths_2_months_prior, two_months_death] = get_total_deaths_2_months_prior(province_name, region_name, end_date)

    #if (c_num == 4):
    #    print("==== \ntotal_deaths_2_months_prior: " + str(total_deaths_2_months_prior))

    for i in range(len(add_dates)):
        date_in_forecast = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=i)
        xAnnual = math.log(annDeath, 10)
        if (first == False):
            xHerd = total_deaths / annDeath  #Total Covid Death/Annual Death -> Annual death as in 2021
            xTrends1 = get_trends_on_day(province_name, region_name, date_in_forecast, facemask_val) # todo: Google Trends for face mask
            xMob1 = get_mob_on_day(df_mobility, date_in_forecast, xMob_slider, 14)
            xMob2 = get_mob_on_day(df_mobility, date_in_forecast, xMob_slider, 28)
            
            #===BPH Weather value is 14d average centered three weeks prior (21d)
            xTemp = get_weather_avg_for_day(df_weather, date_in_forecast, 14, 21)
            
            vaxP1 = get_vac_on_day(date_in_forecast, vac_val, total_population, df_vac, 14, False, last_vac)
            vaxP2 = get_vac_on_day(date_in_forecast, vac_val, total_population, df_vac, 28, False, last_vac)

            if (i <= 60):
                # xHerd2 = total_deaths_2_months_prior / annDeath
                if i<(60-len(two_months_death)):
                    xHerd2 = total_deaths_2_months_prior / annDeath
                else:
                    total_deaths_2_months_prior = \
                        total_deaths_2_months_prior + two_months_death[-(60-i)]
                    xHerd2 = total_deaths_2_months_prior / annDeath
            else:
                deaths_2_months = total_deaths_2_months_prior
                prior = i - 60
                prior_2_months = yVals[0:prior]

                for j in range(len(prior_2_months)):
                    deaths_2_months += prior_2_months[j]

                xHerd2 = deaths_2_months / annDeath
            if (i < 14):
                prior = 14 - i
                deaths_2_weeks = get_total_deaths_2_weeks_prior(province_name, region_name, prior, end_date)
                for j in range(len(yVals)):
                    deaths_2_weeks += yVals[j]
            else:
                deaths_2_weeks = 0.0
                prior_2_weeks = yVals[-14:]
                for j in range(len(prior_2_weeks)):
                    deaths_2_weeks += prior_2_weeks[j]
            
            sigma = math.sqrt(0.093 / (14.0 + deaths_2_weeks))

            exp_ = math.exp(
                        0.5 * (-7.50188 - 34.5879 * (xHerd - xHerd2) - 1.51981 * xHerd2 +
                        0.011227 * xMob1 + 0.0296737 * xMob2 +
                        0.00476657 * (-26.5794 + xTemp)**2 +
                        0.000143682 * (-26.5794 + xTemp)**3 - 0.0244824 * xTrends1 +
                        xLogPWPD * math.log(10.0) + math.log(1 - 0.9 * vaxP2) + 
                        (2.0 * math.log(8.0 * 10.0**(-xLogPWPD) * (2.0 - 0.5 * xBeta))) / (4.0 - xBeta)))
                    
            lambda_ = -0.0398673 + exp_ - 0.202278 * (vaxP1 - vaxP2) - 0.00654545 * (-3.65 + xAnnual) + 0.0201251 * (-2.7 + xHouse)
            delta = random.gauss(0.0, sigma)

            lambda_ += delta # Sqrt[0.092/(14 + Death in Past two weeks)

            lambda_values.append(rt_equation(lambda_))
            # lambda_values.append(0)
            deaths_tomorrow = math.exp(lambda_) * deaths_today
            yVals.append(deaths_tomorrow)

                
            deaths_today = deaths_tomorrow
            total_deaths += deaths_today
            annDeath += deaths_today

        else:
            first = False
            yVals.append(last_mort)
            total_deaths += last_mort
            # annDeath += last_mort

        # y = math.exp(.5*(lS0 + math.log(10)*xLogPWPD + math.log(0.25) + #clarify log 0.25 and 10
        #  2/(4 - xBeta)*math.log((2 - xBeta/2)/(2*10^xLogPWPD*.25^2)) - 
        #  H0*xHerd - H2*(xHerd - xHerd2)*6 - v1*Vax1 + mob1*xMob + 
        #  trend1*xTrends1 + dT2*(xTemp - Tmin2)^2 + dT3*(xTemp - Tmin2)^3 -
        #   math.log(tau))) - 1/tau + house2*(xHouse - 2.75) + Anl*(xAnnual - 3.65) - v2*Vax2 # y = lambda
        # cases_today = 
        # yVals.append(y)

    return yVals, moving_avg(lambda_values, 14)

def predicted_cases(province_name, region_name, start_date, end_date, days_to_forecast, df_mobility, xMob_slider, facemask_val, vac_val):
    print("todo")

# -------------- MORTALITY HELPER FUNCTIONS --------------
def get_total_deaths(province_name, region_name, start_date, end_date, yes_print):
    start_date_str = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%m-%d-%Y')
    end_date_str = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%m-%d-%Y')

    filtered_df2 = df_mort[df_mort.date_death_report.between(
        start_date_str, end_date_str
    )]
    df_province = filtered_df2[filtered_df2.province == province_name]
    
    deaths = df_province.deaths[df_province.health_region == region_name]

    total_deaths_local = 0 # reset total deaths

    for d in deaths:
        total_deaths_local += d
    
    if (yes_print == True):
        print("returning total deaths: " + str(total_deaths_local))
    
    return total_deaths_local

def get_last_mort(province_name, region_name, start_date, end_date):
    start_date_str = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%m-%d-%Y')
    end_date_str = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%m-%d-%Y')

    filtered_df2 = df_mort[df_mort.date_death_report.between(
        start_date_str, end_date_str
    )]
    df_province = filtered_df2[filtered_df2.province == province_name]
    rolling_avgs = df_province.deaths[df_province.health_region == region_name].rolling(window=7).mean()
    # rolling_avgs_2 = (df_province.deaths[df_province.health_region == region_name]**2).rolling(window=7).mean()

    vals1 = []
    # vals2 = []
    # rolling_avgs_2 = []
    for key in rolling_avgs:
        vals1.append(key)
    # for key in rolling_avgs_2:
    #     vals2.append(key)

    last_mort = np.random.poisson(7.0 * vals1[-1]) / 7.0 # vals1[-1] + random.gauss(0.0, math.sqrt((vals2[-1] - vals1[-1]) ** 2)) / math.sqrt(7.0)
    return last_mort

def date(province_name, region_name, start_date, end_date): # todo: dates are in d-m-y
    start_date_str = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%m-%d-%Y')
    end_date_str = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%m-%d-%Y')

    filtered_df2 = df_mort[df_mort.date_death_report.between(
        start_date_str, end_date_str
    )]
    df_province = filtered_df2[filtered_df2.province == province_name]
    
    ans = df_province[df_province.health_region == region_name]
    date_list = ans['date_death_report'].values
    dates = []
    for i in range(len(date_list)):
        dates.append(str(date_list[i]).split("T")[0])
    
    return dates

def r_avg(province_name, region_name, start_date, end_date): # todo: dates are in d-m-y
    start_date_str = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%m-%d-%Y')
    end_date_str = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%m-%d-%Y')

    filtered_df2 = df_mort[df_mort.date_death_report.between(
        start_date_str, end_date_str
    )]
    df_province = filtered_df2[filtered_df2.province == province_name]
    
    rolling_avgs = df_province.deaths[df_province.health_region == region_name].rolling(window=7).mean()
    # deaths = df_province.deaths[df_province.health_region == region_name]

    vals1 = []
    for key in rolling_avgs:
        vals1.append(key)

    return vals1

def get_total_deaths_2_months_prior(province_name, region_name, end_date):
    date_up_to = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    first_day = df_mort.date_death_report.min().date().strftime('%m-%d-%Y')

    delta_2_months = datetime.timedelta(days=60)
    end_date_2_months_ago = date_up_to - delta_2_months
    end_date_2_months_ago = end_date_2_months_ago.strftime('%m-%d-%Y')
    date_up_to = date_up_to.strftime('%m-%d-%Y')

    df_2_months = df_mort[df_mort.date_death_report.between(
        first_day, end_date_2_months_ago
    )]
    df_province_2_months = df_2_months[df_2_months.province == province_name]
    deaths_2_months = df_province_2_months.deaths[df_province_2_months.health_region == region_name]

    A = df_mort[df_mort.date_death_report.between(
        end_date_2_months_ago, date_up_to)]
    B = A[A.province == province_name]
    twomonths_deaths = B.deaths[B.health_region == region_name].to_list()
        
    total_deaths_2_months = 0 # reset total deaths

    for d in deaths_2_months:
        total_deaths_2_months += d

    return [total_deaths_2_months, twomonths_deaths]
    # date_up_to = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    # first_day = df_mort.date_death_report.min().date().strftime('%m-%d-%Y')

    # delta_2_months = datetime.timedelta(days=60)
    # end_date_2_months_ago = date_up_to - delta_2_months
    # end_date_2_months_ago = end_date_2_months_ago.strftime('%m-%d-%Y')

    # df_2_months = df_mort[df_mort.date_death_report.between(
    #     first_day, end_date_2_months_ago
    # )]
    # df_province_2_months = df_2_months[df_2_months.province == province_name]
    # deaths_2_months = df_province_2_months.deaths[df_province_2_months.health_region == region_name]
    # two_months_death = deaths_2_months.to_list()

    # total_deaths_2_months = 0 # reset total deaths

    # for d in deaths_2_months:
    #     total_deaths_2_months += d

    # return [total_deaths_2_months, two_months_death]

def get_total_deaths_2_weeks_prior(province_name, region_name, days_prior, date_up_to_str):
    date_up_to = datetime.datetime.strptime(date_up_to_str, "%Y-%m-%d")
    delta = datetime.timedelta(days=days_prior)
    first_day = date_up_to - delta
    end_date_2_weeks_ago = date_up_to

    df_2_weeks = df_mort[df_mort.date_death_report.between(
        first_day, end_date_2_weeks_ago
    )]
    df_province_2_weeks = df_2_weeks[df_2_weeks.province == province_name]
    deaths_2_weeks = df_province_2_weeks.deaths[df_province_2_weeks.health_region == region_name]

    total_deaths_2_weeks = 0.0 # reset total deaths

    for d in deaths_2_weeks:
        total_deaths_2_weeks += d

    return total_deaths_2_weeks
        
def cumulative_deaths(province_name, region_name, start_date, end_date): # todo: dates are in d-m-y
    start_date_str = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%m-%d-%Y')
    end_date_str = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%m-%d-%Y')

    filtered_df2 = df_mort[df_mort.date_death_report.between(
        start_date_str, end_date_str
    )]
    df_province = filtered_df2[filtered_df2.province == province_name]
    
    deaths = df_province.cumulative_deaths[df_province.health_region == region_name] #.rolling(window=7).mean()
        
    return deaths
    
# -------------- CASES HELPER FUNCTIONS --------------

def get_last_cases(province_name, region_name, start_date, end_date): # todo: d-m-y
    filtered_df = df_cases[df_cases.date_report.between(
        datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%m-%d-%Y'),
        datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%m-%d-%Y')
    )]
    dfcases_province = filtered_df[filtered_df.province == province_name]
    rolling_avgs = dfcases_province.cases[dfcases_province.health_region == region_name].rolling(window=7).mean()

    cases = []
    for key in rolling_avgs:
        cases.append(key)
    last_cases = cases[-1]

    return last_cases

def date_cases(province_name, region_name, start_date, end_date):# todo: d-m-y
    filtered_df = df_cases[df_cases.date_report.between(
        datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%m-%d-%Y'),
        datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%m-%d-%Y')
    )]
    dfcases_province = filtered_df[filtered_df.province == province_name]
    return dfcases_province.date_report[dfcases_province.health_region == region_name]

def ravg_cases(province_name, region_name, start_date, end_date): # todo: d-m-y
    filtered_df = df_cases[df_cases.date_report.between(
        datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%m-%d-%Y'),
        datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%m-%d-%Y')
    )]
    dfcases_province = filtered_df[filtered_df.province == province_name]
    rolling_avgs = dfcases_province.cases[dfcases_province.health_region == region_name].rolling(window=7).mean()

    cases = []
    for key in rolling_avgs:
        cases.append(key)

    return cases

def get_total_cases(province_name, region_name, start_date, end_date):
    start_date_str = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_str = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')

    filtered_df2 = df_cases[df_cases.date_report.between(
        start_date_str, end_date_str
    )]
    df_province = filtered_df2[filtered_df2.province == province_name]
    
    cases = df_province.cases[df_province.health_region == region_name]

    total_cases_local = 0

    for c in cases:
        total_cases_local += c
    
    return total_cases_local

# -------------- MOBILITY HELPER FUNCTIONS --------------

def mobility(province_name, region_name, start_date, end_date):
    filtered_df = mobility_info[mobility_info.date.between(
        start_date, end_date
    )]
    weat_info_province = static_data[static_data.province_name == province_name]
    sub_region = weat_info_province.sub_region_2[weat_info_province.health_region == region_name].item()

    return filtered_df.workplaces_percent_change_from_baseline[mobility_info.sub_region_2 == sub_region].rolling(window=7).mean()

def date_mob(province_name, region_name, start_date, end_date):
    filtered_df = mobility_info[mobility_info.date.between(
        start_date, end_date
    )]
    
    weat_info_province = static_data[static_data.province_name == province_name]
    sub_region = weat_info_province.sub_region_2[weat_info_province.health_region == region_name].item()
    
    return filtered_df.date[mobility_info.sub_region_2 == sub_region]

def interpolate_mob_dates(province_name, region_name, start_date, end_date, days_to_forecast):

    base = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    add_dates = [base + datetime.timedelta(days=x) for x in range(days_to_forecast * 30)]

    for i in range(len(add_dates)):
        add_dates[i] = datetime.datetime.strptime(str(add_dates[i]), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
    
    return add_dates

def get_mob_on_day(df_mobility, day, xMob, days_prior):
    #===BPH accept df_mobility as an argument now
    first_date_str = df_mobility['date'].iloc[0]
    first_date = datetime.datetime.strptime(first_date_str, "%Y-%m-%d").date()
    
    days_since_first_day = day.date() - first_date - datetime.timedelta(days=days_prior)
    delta = days_since_first_day.days - 1 - 5 # todo: remove -5

    #===BPH-FIXME Should be a better way to grab mobility on a day
    if (delta < len(df_mobility) and delta >= 0):
        mob = df_mobility['workplaces_percent_change_from_baseline'].iloc[delta]
    else:
        mob = xMob

    return mob

def get_last_mob(df_mobility):
    #===BPH accept df_mobility as an argument now
    total_mob_records = len(df_mobility) - 1
    today_mob = df_mobility['workplaces_percent_change_from_baseline'].iloc[total_mob_records]
    last_mob = -today_mob

    return last_mob

def get_mob(province_name, region_name):
    weat_info_province = static_data[static_data.province_name == province_name]
    sub_region = weat_info_province.sub_region_2[weat_info_province.health_region == region_name].item()
    mobs = mobility_info[mobility_info.sub_region_2 == sub_region]
    filtered = mobs[['date', 'workplaces_percent_change_from_baseline']]
    return filtered

# -------------- WEATHER HELPER FUNCTIONS --------------

def get_weather_dataframe(province_name, region):
    #===BPH Get weather dataframe
    #
    #  File contains data from 2020-01-01 -- 2023-01-01.  Data in temp_mean
    #  is actual temperature up until current date, then the four-year average
    #  of the prior years after the current date.  Four-year average is also
    #  given for all dates.
    #
    #  columns = [date, temp_mean, temp_min, temp_max, climate_id,
    #             theta, temp_mean_avg, temp_min_avg, temp_max_avg]
    #
    #
    # create file name
    prov_id = get_provinceid(province_name, region)
    hr_uid = get_hruid(province_name, region)
    weatherfile = prov_id + "_" + str(hr_uid) + ".csv"
    # read in data
    df_weather = pd.read_csv(weather_data_dir + weatherfile)
    # convert date column to datetime
    df_weather['date'] = pd.to_datetime(df_weather['date'])
    return df_weather


def get_weather_avg_for_day(df_weather, day, avg_window_days, avg_window_center_days_prior):
    # filter dataframe on averaging window
    window_centerdate = day - datetime.timedelta(days=avg_window_center_days_prior)
    window_halfwidth = datetime.timedelta(days = avg_window_days/2.0)
    window_start = window_centerdate - window_halfwidth
    window_end = window_centerdate + window_halfwidth    
    df = df_weather[df_weather.date.between(window_start, window_end)]

    # return average temperature
    return df['temp_mean'].mean()



def get_current_temp_dates_vals(temp_files):
    dates = []
    temps = []
    for file in temp_files:
        weat_data =  pd.read_csv(file, encoding='Latin-1')
        temp_dates = weat_data['Date/Time'].values
        dates.extend(temp_dates)
        temp_dates = weat_data['Mean Temp (°C)'].values
        temps.extend(temp_dates)
    return dates, temps

def get_past_temp_dates_vals(temp_files):
    dates = []
    temps = []
    for file in temp_files:
        weat_data = pd.read_csv(file, encoding='Latin-1')
        weat_data['Date/Time'] = pd.to_datetime(weat_data['Date/Time'], errors='coerce')
        formatted_dates = weat_data['Date/Time'].dt.strftime('%m-%d')
        temp_dates = formatted_dates.values
        dates.extend(temp_dates)
        temp_dates = weat_data['Mean Temp (°C)'].values
        temps.extend(temp_dates)
    return dates, temps

def get_current_temp_files(province_name, region, start_date, end_date):
    date_now_str = datetime.datetime.now().strftime('%Y-%m')

    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    num_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
    temp_files = []

    prov_id = get_provinceid(province_name, region)
    climate_id = climateid(province_name, region)

    for i in range(num_months): # todo: what if file doesn't exist
        year = start_date.year
        month = start_date.month + i
        if (month > 12): # todo: change to shafika's
            year = year + 1
            month = month % 12
        
        if (month < 10):
            month = "0" + str(month)
        else:
            month = str(month)

        date_now_str = str(year) + "-" + month 
        target_url = weather_base_url + prov_id + '/climate_daily_' + prov_id + '_' + climate_id + '_' + date_now_str + '_P1D.csv'
        temp_files.append(target_url)

    return temp_files

def get_past_temp_files(province_name, region_name, start_date, end_date):
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    num_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
    temp_files = []

    prov_id = get_provinceid(province_name, region_name)
    climate_id = climateid(province_name, region_name)

    for year in range(start_date.year, end_date.year+1):
        year = str(year)
        for month in range(1,13):
            if month in range(1,10):
                month = '0' + str(month)
            else:
                month = str(month)

            gloabl_date = str(year) + "-" + month
            target_url = weather_base_url + prov_id + '/climate_daily_' + prov_id + '_' + climate_id + '_' + gloabl_date + '_P1D.csv'
            temp_files.append(target_url)

    return temp_files

# -------------- VACCINATION HELPER FUNCTIONS --------------

def get_uid(province_name, region_name):
    uid = get_region_info(province_name, region_name).hr_uid.item()
    return uid

def get_vaccination_dates(province_name, region_name):
    vac_date = []
    for d in vaccination_data(province_name, region_name):
        time = d['date']
        vac_date.append(time)
        
    return vac_date
    
def get_vaccination_vals(province_name, region_name):
    total_vaccinations = []
    for d in vaccination_data(province_name, region_name):
        vaccine = d['total_vaccinations']
        total_vaccinations.append(vaccine)

    return total_vaccinations

def get_last_vac(province_name, region_name):
    total_vaccinations = []
    for d in vaccination_data(province_name, region_name):
        vaccine = d['total_vaccinations']
        total_vaccinations.append(vaccine)

    last_vac = total_vaccinations[len(total_vaccinations) - 1]

    return last_vac

def get_vac_on_day(date_in_forecast, vac_val, total_population, df_vac, days_prior, yes_print, last_vac):
    vac_vals = []

    found_first_day = False
    for day in df_vac:
        if (found_first_day == False and day["total_vaccinations"] != None):
            first_day_vac_str = day["date"]
            found_first_day = True
        elif (day["total_vaccinations"] != None):
            vaccine = day['total_vaccinations']
            vac_vals.append(vaccine)
            last_vac_date_str = day["date"]


    first_day_vac_date = datetime.datetime.strptime(first_day_vac_str, '%Y-%m-%d')
    last_vac_date = datetime.datetime.strptime(last_vac_date_str, '%Y-%m-%d')
    days_since_first_day = date_in_forecast.date() - first_day_vac_date.date() - datetime.timedelta(days=days_prior)
    delta = days_since_first_day.days

    days_since_last_day = (date_in_forecast.date() - last_vac_date.date()).days

    if (delta < len(vac_vals) and delta >= 0):
        vac = vac_vals[delta] / total_population
    elif (delta < 0):
        vac = 0.0
    else:
        temp = vac_val * total_population * (days_since_last_day) / 7.0
        vac = last_vac + temp
        vac = vac / total_population
        vac = min(vac, 1.0)
    
    return vac

def vac_df_data(province_name, region_name):
    vac_data = {'date':  get_vaccination_dates(province_name, region_name),
        'total_vaccinations': get_vaccination_vals(province_name, region_name)}
    return vac_data

def vaccination_data(province_name, region_name):
    vac_base_url = "https://api.covid19tracker.ca/reports/regions/"
    vac_base_url_prov = "https://api.covid19tracker.ca/reports/province/"

    if (province_name == 'Alberta') or (province_name == 'New Brunswick') or (province_name == 'NL') or (province_name == 'Nova Scotia'):
        api = vac_base_url_prov + str(get_provinceid(province_name, region_name))

    else:
        api = vac_base_url + str(int(get_uid(province_name, region_name)))
    
    with request.urlopen(str(api)) as response:
        source = response.read()
        api_data = json.loads(source)['data']  

    return api_data

def df_vaccinations(province_name, region_name):    
    df_vaccinations = pd.DataFrame(vac_df_data(province_name, region_name), columns = ['date','total_vaccinations'])
    df_vaccinations = df_vaccinations.dropna()
    if (province_name == 'Alberta') or (province_name == 'New Brunswick') or (province_name == 'NL') or (province_name == 'Nova Scotia'):
        df_vaccinations['total_vaccinations'] = df_vaccinations.total_vaccinations.div(get_prov_pop(province_name, region_name))
    else:
        df_vaccinations['total_vaccinations'] = df_vaccinations.total_vaccinations.div(get_total_pop(province_name, region_name))
    
    return df_vaccinations

def get_frac_vaccinations_1_month_prior(province_name, region_name):
    date_now = datetime.datetime.now() #datetime.datetime.now()
    first_day =df_vac.date.min()
    
    delta_1_month = datetime.timedelta(days=30)
    end_date_1_month_ago = date_now - delta_1_month
    end_date_1_month_ago = end_date_1_month_ago.strftime('%Y-%m-%d')
        
    df_1_month = df_vac[df_vac.date.between(
        first_day, end_date_1_month_ago
    )]

    return df_1_month.mean().item()

def get_frac_vaccinations_2_weeks_prior(province_name, region_name, days_prior):
    
    date_now = datetime.datetime.now() #datetime.datetime.now()
    delta = datetime.timedelta(days=days_prior)
    first_day = date_now - delta
    first_day = first_day.strftime('%d-%m-%Y')
    end_date_2_weeks_ago = date_now
    
    df_2_weeks = df_vac[df_vac.date.between(
        first_day, end_date_2_weeks_ago
    )]
    
    return df_2_weeks


# -------------- GOOGLE TRENDS HELPER FUNCTIONS --------------

def get_geocode(province_name, region_name):
    geo_code = get_region_info(province_name, region_name).geo_code.item()
    return geo_code

def get_trends_vals(province_name, region_name):
    return df_trends[str(get_geocode(province_name, region_name))]

def get_trends_dates(province_name, region_name):
    return df_trends['date']

def df_trends_data(province_name, region_name):
    trends_data = {'date': get_trends_dates(province_name, region_name),
        str(get_geocode(province_name, region_name)): get_trends_vals(province_name, region_name)}
    df_trends = pd.DataFrame(trends_data, columns = ['date', str(get_geocode(province_name, region_name))])
    return df_trends

def get_trends_on_day(province_name, region_name, day, trends):
    days_since_first_day = day.date() - datetime.date(2020, 1, 1)
    delta = days_since_first_day.days - 43 - 11 # todo: remove - 11
    df_dates = df_trends[str(get_geocode(province_name, region_name))]
    if (delta < len(df_trends.index) and delta >= 0):
        trend_42_days_ago = df_dates[delta]
        if (province_name == "Quebec"):
            trend_42_days_ago = trend_42_days_ago * 2.5
    else:
        trend_42_days_ago = trends
        
    return trend_42_days_ago

def get_last_trends(province_name, region_name):
    df_dates = df_trends[str(get_geocode(province_name, region_name))]
    return df_dates[len(df_trends.index) - 1]


# -------------- REPRODUCTIVE NUMBER HELPER FUNCTIONS --------------

# Rt curve: R(t) =exp(lambda(t)*5.3)
# Rt for past data= D14(t)/D14(t-5)

def rt_equation(lambda_):
    return math.exp((lambda_*5.3))

def get_total_deaths_2_weeks_prior(province_name, region_name, days_prior, date_up_to_str):	
    date_up_to = datetime.datetime.strptime(date_up_to_str, "%Y-%m-%d")	
    delta = datetime.timedelta(days=days_prior)
    first_day = date_up_to - delta # todo: date_up_to
    # first_day = first_day.strftime('%d-%m-%Y')
    end_date_2_weeks_ago = date_up_to # todo: date_up_to
    df_2_weeks = df_mort[df_mort.date_death_report.between(
        first_day, end_date_2_weeks_ago
    )]
    df_province_2_weeks = df_2_weeks[df_2_weeks.province == province_name]
    deaths_2_weeks = df_province_2_weeks.deaths[df_province_2_weeks.health_region == region_name]
    total_deaths_2_weeks = 0.0 # reset total deaths	
    for d in deaths_2_weeks:
        total_deaths_2_weeks += d

    return total_deaths_2_weeks

def rt_equation(lambda_):
    return math.exp((lambda_*5.3))

def past_rt_equation(province_name, region_name):
    
    D14_values = []
    D14_t5_values = []
    
    date_D14 = datetime.datetime.today()
    date_D14_t5 = date_D14 - datetime.timedelta(days=4)
    days_prior = 14
    
    start = datetime.datetime.strptime("2020-03-08", "%Y-%m-%d")
    end = date_D14
    end = end.strftime("%Y-%m-%d")
    end = datetime.datetime.strptime(str(end), "%Y-%m-%d")
    date_generated = [start + datetime.timedelta(days=x) for x in range(0, (end-start).days+1)]
    for date in date_generated:
        date_range = date.strftime("%Y-%m-%d")
        D14 = get_total_deaths_2_weeks_prior(province_name, region_name, days_prior, date_range)
        #D14 = get_total_cases_2_weeks_prior(province_name, region_name, days_prior, date_range)
        D14_values.append(D14)	
        
    
    # Shifted the start date by 5 days
    start = datetime.datetime.strptime("2020-03-04", "%Y-%m-%d")
    end = date_D14_t5
    end = end.strftime("%Y-%m-%d")
    end = datetime.datetime.strptime(str(end), "%Y-%m-%d")
    date_generated = [start + datetime.timedelta(days=x) for x in range(0, (end-start).days+1)]
    for date in date_generated:
        date_range = date.strftime("%Y-%m-%d")
        D14_t5 = get_total_deaths_2_weeks_prior(province_name, region_name, days_prior, date_range)
        #D14_t5 = get_total_cases_2_weeks_prior(province_name, region_name, days_prior, date_range)
        D14_t5_values.append(D14_t5)
        
    
    D14_values = [x+0.5 for x in D14_values]
    D14_t5_values = [x+0.5 for x in D14_t5_values]    
    
    past_data = [x / y if y != 0 else 0.0 for x, y in zip(D14_values, D14_t5_values)]
    
    past_data = np.clip(past_data, -3, 10)
        
    return moving_avg(past_data, 14)

def moving_avg(x, n):
    cumsum = np.cumsum(np.insert(x, 0, 0))
    return (cumsum[n:] - cumsum[:-n]) / float(n)

# ======================= END OF PROGRAM =======================

if __name__ == "__main__":
    app.run_server(debug=True)