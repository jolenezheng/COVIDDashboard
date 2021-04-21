# -*- coding: utf-8 -*-
import math
import dash
import dash_table
import random
import requests
import time
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
import numpy as np
from dash.dependencies import Output, Input, State
import plotly.express as px
import plotly.graph_objects as go
import datetime as datetime

from textwrap import dedent
from dateutil.relativedelta import relativedelta

from pages import *


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

weather_base_url = 'https://dd.weather.gc.ca/climate/observations/daily/csv/' # todo: accented names?
static_data = pd.read_csv(r'data/health_regions_static_data.csv', encoding='Latin-1')

# mobility_info = pd.read_csv(r'data/mobility_test.csv')
mobility_info = pd.read_csv(r'data/mobility.csv')
mobility_info["sub_region_2"] = mobility_info["sub_region_2"]
df_mobility = None

df_trends = pd.read_csv(r'data/google_trends_face_mask_canada.csv')

df_vac = pd.DataFrame({'Init' : []})

prov_id = "ON"
climate_id = 0
target_url = ""
weat_data = None
weat_city = None
date_city = None
total_deaths = 0

avg_temp_vals = []

initial_load = True
prev_states = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]


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

footer = dbc.Navbar(
    [
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(dbc.NavbarBrand("Footer", className="ml-2")),
                ],
                align="center",
                no_gutters=True,
            ),
        ),
    ],
    color="dark",
    dark=True,
    sticky="bottom"
)

footer2 = html.Footer(html.Div([
    "Dashboard made by Jolene Zheng and Shafika Olalekan Koiki | ",
    html.A(" GitHub", href="https://github.com/jolenezheng/COVIDDashboard/", target="_blank")
], className="footer"))

site_backbone = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(navbar2),
    html.Div(id='page-content', className="page border"),
    # html.Div("", className="push"),
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
                                                    children="Face Mask Use",
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
                                                    children="Reduction in Social Mobility vs Baseline",
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
                                                    children="Vaccination",
                                                    className="dropdown-title"
                                                    ),
                                                dcc.Slider(
                                                    id='vaccine-slider',
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
                                                    children="Date to Start Forecast",
                                                    className="dropdown-title",
                                                    ),
                                                dcc.DatePickerSingle(
                                                    id="forecast-start-date",
                                                    min_date_allowed=df_mort.date_death_report.min().date(),
                                                    max_date_allowed=df_mort.date_death_report.max().date(), # df_mort.date_death_report.max().date(),
                                                    initial_visible_month=df_mort.date_death_report.max().date(),
                                                    date= "2020-11-01", # df_mort.date_death_report.max().date(), # "2020-11-01"
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
                                                    value=9, # todo: change back to 3
                                                    marks={ 0: '0 mo', 2: '2 mo', 4: '4 mo',
                                                        6: '6 mo', 8: '8 mo', 10: '10 mo', 12: '1 yr'
                                                    },
                                                ),
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            dbc.Button("Rerun", id='rerun-btn', n_clicks=0, color="dark", className="mr-1"),
                                            # html.Button('Rerun', id='rerun-btn', n_clicks=0),
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
                                                html.H5(id="total-pop-card",className="card-title"),
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
                                        dbc.CardHeader("Population Sparsity"),
                                        dbc.CardBody(
                                            [
                                                html.H5(id="sparsity-card",className="card-title"),
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
                                                html.H5(id="frac-pop-card", className="card-title"),
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
                                        dbc.CardHeader("Population Weighted Population Density"),
                                        dbc.CardBody(
                                            [
                                                html.H5(id="pwpd-card", className="card-title"),
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
                                                html.H5(id="avg-house-card", className="card-title"),
                                            ]
                                        ),
                                    ],
                                    color="dark",
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
                    #     dbc.Row([	
                    #         dbc.Col(	
                    #             dbc.Card(	
                    #                 [	
                    #                     dbc.CardHeader(id="rtcurve-header"),
                    #                     dbc.CardBody(
                    #                         dcc.Loading(
                    #                             children=[html.Div(dcc.Graph(
                    #                                 id="rtcurve-chart", config={"displayModeBar": False}))],
                    #                             type="default"
                    #                     )),
                    #                 ], color="dark", inverse=True),	
                    #         ),	
                    # ], className="mb-4")
                    ]),
                    className="column",
                    xl=9, lg=9, md=12, sm=12, xs=12,
                ),
            ], className="mb-4"
        ),
    ],
)

@app.callback(
    dash.dependencies.Output('page-content', 'children'),
    [dash.dependencies.Input('url', 'pathname')]
)
def display_page(pathname):
    # print("URL IS: " + pathname)
    if (pathname == "/"):
        return canadian_dashboard
    elif (pathname == "/about"):
        return about_page
    elif (pathname == "/faq"):
        return faq_page2
    elif (pathname == "/intro"):
        return introduction_page
    
    return canadian_dashboard

# FAQ Page
@app.callback(
    [
        Output("a1", "is_open"), Output("a2", "is_open"), Output("a3", "is_open"), Output("a4", "is_open"),
        Output("a5", "is_open"), Output("a6", "is_open"), Output("a7", "is_open"), Output("a8", "is_open"),
        Output("a9", "is_open"), Output("a10", "is_open"), Output("a11", "is_open"), Output("a12", "is_open"),
        Output("a13", "is_open"), Output("a14", "is_open"), Output("a15", "is_open")
    ],
    [
        Input("q1", "n_clicks"), Input("q2", "n_clicks"), Input("q3", "n_clicks"), Input("q4", "n_clicks"),
        Input("q5", "n_clicks"), Input("q6", "n_clicks"), Input("q7", "n_clicks"), Input("q8", "n_clicks"),
        Input("q9", "n_clicks"), Input("q10", "n_clicks"), Input("q11", "n_clicks"), Input("q12", "n_clicks"),
        Input("q13", "n_clicks"), Input("q14", "n_clicks"), Input("q15", "n_clicks")
    ],
    [
        State("a1", "is_open"), State("a2", "is_open"), State("a3", "is_open"), State("a4", "is_open"),
        State("a5", "is_open"), State("a6", "is_open"), State("a7", "is_open"), State("a8", "is_open"),
        State("a9", "is_open"), State("a10", "is_open"), State("a13", "is_open"), State("a12", "is_open"),
        State("a13", "is_open"), State("a14", "is_open"), State("a15", "is_open")
    ],
)
def toggle_collapse(q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14, q15, is_open1, is_open2, is_open3, is_open4, is_open5, is_open6, is_open7, is_open8, is_open9, is_open10, is_open11, is_open12, is_open13, is_open14, is_open15):
    questions = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14, q15]
    states = [is_open1, is_open2, is_open3, is_open4, is_open5, is_open6, is_open7, is_open8, is_open9, is_open10, is_open11, is_open12, is_open13, is_open14, is_open15]
    global prev_states

    for i in range(15):
        q = questions[i]
        if q and q != prev_states[i]:
            states[i] = not states[i]
            prev_states[i] = questions[i]
        
    return states


@app.callback(
    [
        Output("facemask-slider", "value"),
        Output("mobility-slider", "value"),
        Output("vaccine-slider", "value"),
        Output("forecast-slider", "value"),
    ],
    [
        dash.dependencies.Input('region-dropdown', 'value'), 
        dash.dependencies.Input('subregion-dropdown', 'value'), 
        Input("forecast-start-date", "date"),
    ]
)
def init_slider_vals(province_name, region_name, date_str):
    global df_mobility
    df_mobility = get_mob(province_name, region_name)
    date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    global initial_load

    # vac_dates = get_vaccination_dates(province_name, region_name)
    df_vac = vaccination_data(province_name, region_name)

    if (initial_load):
        mob = get_last_mob()
        trends = get_last_trends(province_name, region_name)
        vac = get_last_vac(province_name, region_name) / round(get_total_pop(province_name, region_name), 0) * 100
    else:
        mob = -get_mob_on_day(date, 0, 0)
        # trends = get_last_trends(province_name, region_name)
        trends = get_trends_on_day(province_name, region_name, date, 0)
        vac = get_vac_on_day(date, 0, -1, df_vac, 0)
    initial_load = False
    # print("setting slider vac to be: " + str(vac) + " for day: " + str(date))
    return trends, mob, vac, 3 # todo: change 0 -> vac

@app.callback(
    [
        dash.dependencies.Output('total-pop-card', 'children'),
        dash.dependencies.Output('sparsity-card', 'children'),
        dash.dependencies.Output('frac-pop-card', 'children'),
        dash.dependencies.Output('pwpd-card', 'children'),
        dash.dependencies.Output('avg-house-card', 'children'),
        Output("simulation-header", "children"),
        Output("cases-header", "children"),
        Output("mob-header", "children"),
        Output("temp-header", "children"),
        Output("vac-header", "children"),
        Output("trends-header", "children"),
        # Output("rtcurve-header", "children"),
    ],
    [dash.dependencies.Input('region-dropdown', 'value'), dash.dependencies.Input('subregion-dropdown', 'value'),]
)
def update_region_names(province_name, region_name):
    global df_vac
    df_vac = df_vaccinations(province_name, region_name)

    # Card Values
    total_pop = round(get_total_pop(province_name, region_name), 0)
    sparsity = round(get_pop_sparsity(province_name, region_name), 3)	
    pop_80 = round(get_frac_pop_over_80(province_name, region_name), 3)	
    pwpd = round(get_pwpd(province_name, region_name), 0)

    # todo: sparsity (3 digits)
    # pop_80 = round(get_frac_pop_over_80(province_name, region_name), 2)
    # pwpd = round(get_pwpd(province_name, region_name), 2)
    avg_house = round(get_avg_house(province_name, region_name), 2)
    # Graph Titles
    deaths_label = 'Daily Predicted Deaths in ' + region_name + ', ' + province_name
    cases_label = 'Daily Reported Cases in ' + region_name + ', ' + province_name
    mob_label = 'Social Mobility in ' + region_name + ', ' + province_name
    temp_label = 'Daily Reported Temperature in ' + region_name + ', ' + province_name
    vac_label = 'Fraction of the Population Vaccinated in ' + region_name + ', ' + province_name
    trends_label = 'Google Searches for Face Masks in ' + region_name + ', ' + province_name
    rtcurve_label = 'Future Effective Reproduction Number R(t) Curves in ' + region_name + ', ' + province_name
    return total_pop, sparsity, pop_80, pwpd, avg_house, deaths_label, cases_label, mob_label, temp_label, vac_label, trends_label # , rtcurve_label


@app.callback(
    dash.dependencies.Output('subregion-dropdown', 'options'),
    [dash.dependencies.Input('region-dropdown', 'value')]
)
def update_date_dropdown(name):
    return [{'label': i, 'value': i} for i in fnameDict[name]]

# def display_info_box(btn_click):
#     if (btn_click % 2) == 1:
#         return dedent(extend_intro), "Close"
#     else:
#         return dedent(base_intro), "Learn More"


 # ============== SLIDER CALLBACK ==============

# @app.callback(Output('slider-drag-output', 'children'),
#               [Input('facemask-slider', 'drag_value'), Input('facemask-slider', 'value')])
# def display_value(drag_value, value):
#     return 'For testing purposes: Drag Value: {} | Value: {}'.format(drag_value, value)

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
    Output("simulation-chart", "figure"),
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("forecast-start-date", "date"),
        Input('forecast-slider', 'value'),
        Input('facemask-slider', 'value'),
        Input('mobility-slider', 'value'),
        Input('vaccine-slider', 'value'),
        Input('rerun-btn', 'n_clicks')
    ],
)
def update_mortality_chart(province_name, region, start_date, end_date, day_to_start_forecast, days_to_forecast, facemask, xMob, vac, n_clicks):
    province_name = update_province_name(province_name)
    xMob = -xMob
    facemask = facemask * 70 / 100
    vac = vac / 100.0
    today = datetime.datetime.now()
    death_dates = date(province_name, region, start_date, today.strftime("%Y-%m-%d"))
    death_vals = r_avg(province_name, region, start_date, end_date)

    global df_mobility
    df_mobility = get_mob(province_name, region)
    pred_fig = go.Figure()

    df_vac = vaccination_data(province_name, region)

    # fig.update_xaxes(type="log", range=[0,5])
    time.sleep(2)
    for i in range(10):
        if (i == 0):
            time.sleep(4)
        elif(i == 1):
            time.sleep(3)
        # print("===== CURVE: " + str(i) + " ========")
        dates = predicted_dates(province_name, region, start_date, day_to_start_forecast, days_to_forecast)
        deaths = predicted_deaths(province_name, region, start_date, day_to_start_forecast, days_to_forecast, df_mobility, xMob, facemask, vac, df_vac)[0]
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

    updatemenus = [
        dict(
            type="buttons",
            xanchor="right",
            yanchor="bottom",
            direction="left",
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
    pred_fig.update_layout(xaxis_title='Date',
                   yaxis_title='Daily Mortality (7-day Rolling Avg)',
                   updatemenus=updatemenus)

    return pred_fig

@app.callback(
    Output("cases-chart", "figure"), # Output("map1", "figure"), Output("map2", "figure")],
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("forecast-start-date", "date"),
        Input('forecast-slider', 'value'),
        Input('facemask-slider', 'value'),
        Input('mobility-slider', 'value'),
        Input('vaccine-slider', 'value'),
    ],
)
def update_cases_charts(province_name, region, start_date, end_date, day_to_start_forecast, days_to_forecast, facemask, xMob, vac):
    province_name = update_province_name(province_name)
    xMob = -xMob
    facemask = facemask * 70 / 100
    vac = vac / 100.0
    today = datetime.datetime.now()
    cases_dates = date(province_name, region, start_date, today.strftime("%Y-%m-%d"))
    cases_vals = ravg_cases(province_name, region, start_date, today.strftime("%Y-%m-%d"))

    global df_mobility
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

    updatemenus = [
        dict(
            type="buttons",
            xanchor="right",
            yanchor="bottom",
            direction="left",
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

    cases_fig.update_layout(xaxis_title='Date',
                   yaxis_title='Daily Cases (7-day Rolling Avg)',
                   updatemenus=updatemenus)

    return cases_fig

@app.callback(
    Output("weather-chart", "figure"),
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input('forecast-slider', 'value'), # todo: this isn't really needed to improve performance
    ],
)
def update_weather_chart(province_name, region, start_date, end_date, forecasted_dates):
    date_now = datetime.datetime.now()
    temp_files = get_temp_files(province_name, region, start_date, end_date)
    temp_dates = get_temp_dates(temp_files)
    temp_vals = get_temp_vals(temp_files)

    new_dates = predicted_dates(province_name, region, start_date, end_date, forecasted_dates)

    # temp_files = get_temp_files(province_name, region, start_date, end_date)
    data = {'Date':  get_temp_dates(temp_files),
        'Mean Temperature': get_temp_vals(temp_files)}
    forecasted = datetime.timedelta(days=forecasted_dates)

    df_weather = pd.DataFrame(data, columns = ['Date', 'Mean Temperature'])	
    forecasted = datetime.timedelta(days=forecasted_dates)	
    weather_fig = px.line(df_weather, x = df_weather['Date'], y = df_weather['Mean Temperature'].rolling(window=14).mean())	
    weather_fig.update_layout(xaxis_title='Date',	
                   yaxis_title='Mean Temperature')	
    weather_fig.add_trace(go.Scatter(	
            x=new_dates,	
            y=avg_temp_data(date_now, date_now + forecasted, data),	
            name='Historical Average',	
        ))

    # weather_fig = px.line(df_mort, x = temp_dates, y = temp_vals)
    # weather_fig.update_layout(xaxis_title='Date',
    #                yaxis_title='Mean Temperature')
    # weather_fig.add_trace(go.Scatter(
    #         x=new_dates,
    #         y=avg_temp_data(date_now, date_now + forecasted, data),
    #         name='Average Temp in Last 5 Years',
    #     ))
    
    return weather_fig

@app.callback(
    Output("mobility-chart", "figure"),
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input('forecast-slider', 'value'),
        Input('mobility-slider', 'value'),
    ],
)
def update_mob_charts(province_name, region, start_date, end_date, forecasted_dates, xMob):
    province_name = update_province_name(province_name)
    xMob = -xMob
    dates = predicted_dates(province_name, region, start_date, end_date, forecasted_dates)
    mob_values = []
    for i in range(len(dates)):
        mob_values.append(xMob)
    
     # ============== MOBILITY GRAPH ==============
    mobility_fig = px.line(df_mort, x = date_mob(province_name, region, start_date, end_date), y = mobility(province_name, region, start_date, end_date))
    mobility_fig.update_layout(xaxis_title='Date',
                   yaxis_title='Social Mobility')
    mobility_fig.add_trace(go.Scatter(
            x=dates,
            y=mob_values,
            name='Simulated Mobility',
        ))
    
    return mobility_fig

@app.callback(
    Output("vac-chart", "figure"),
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
    ],
)
def update_vaccination_charts(province_name, region):
    province_name = update_province_name(province_name)
    df_vac = vaccination_data(province_name, region)
    total_population = get_total_pop(province_name, region)
    # vac_dates = df_vac.date
    # vac_vals = df_vac.total_vaccinations

    vac_dates = []
    vac_vals = []

    for day in df_vac:
        if (day["total_vaccinations"] != None):
            date = day['date']
            vac_dates.append(date)
            vaccine = day['total_vaccinations'] / total_population
            vac_vals.append(vaccine)
        
    vaccination_fig = px.line(vac_vals, x = vac_dates, y = vac_vals)
    vaccination_fig.update_layout(xaxis_title='Date',
                   yaxis_title='Total Vaccinations/Population of Region')

    return vaccination_fig

@app.callback(
    Output("trends-chart", "figure"),
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
    ],
)
def update_trends_charts(province_name, region):
    province_name = update_province_name(province_name)

    # ============== GOOGLE TRENDS GRAPH ==============
    df_trends = df_trends_data(province_name, region)
    trends_fig = px.line(df_trends, x = df_trends['date'], y = df_trends[str(get_geocode(province_name, region))])
    trends_fig.update_layout(xaxis_title='Date',
                   yaxis_title='Number of Google Searches for Face Masks')

    return trends_fig


# @app.callback(	
#     Output("rtcurve-chart", "figure"),	
#     [	
#         Input("region-dropdown", "value"),	
#         Input("subregion-dropdown", "value"),	
#         Input("date-range", "start_date"),	
#         Input("date-range", "end_date"),	
#         Input("forecast-start-date", "date"),	
#         Input('forecast-slider', 'value'),	
#         Input('facemask-slider', 'value'),	
#         Input('mobility-slider', 'value'),	
#         Input('vaccine-slider', 'value'),   	
#     ],	
# )	
# def update_rtcurve_charts(province_name, region, start_date, end_date, day_to_start_forecast, days_to_forecast, facemask, xMob, vac):	
    # province_name = update_province_name(province_name)	
    # xMob = -xMob	
    # facemask = facemask * 70 / 100	
    # vac = vac / 100.0	
    	
    # global df_mobility	
    # df_mobility = get_mob(province_name, region)    	
    # df_vac = vaccination_data(province_name, region)

    	
    # rtcurve_fig = go.Figure()	
    	
    # # ============== R(T) CURVE GRAPH ==============	
    # for i in range(10):    	
    #     rtcurve_fig.add_trace(go.Scatter(	
    #         x=predicted_dates(province_name, region, start_date, end_date, days_to_forecast),	
    #         y=predicted_deaths(province_name, region, start_date, day_to_start_forecast, days_to_forecast, df_mobility, xMob, facemask, vac, df_vac)[1],	
    #     name = 'R(t)'	
    # ))
    	
    # start = datetime.datetime.strptime("2020-03-08", "%Y-%m-%d")	
    # end = datetime.datetime.today()	
    # end = end.strftime("%Y-%m-%d")	
    # end = datetime.datetime.strptime(str(end), "%Y-%m-%d")	
    # date_generated = [start + datetime.timedelta(days=x) for x in range(0, (end-start).days+1)]	
    # for date in date_generated:	
    #     date_range = date.strftime("%Y-%m-%d")	
    	
    # rtcurve_fig.add_trace(go.Scatter(	
    #         x=date(province_name, region, start_date, end_date),	
    #         y=past_rt_equation(province_name, region),	
    #         name='Previous R(t)',	
    #         line=dict(color='black', width=2),	
    # ))	
    	
    # rtcurve_fig.update_layout(xaxis_title='t',	
    #                yaxis_title='R(t)')	
    	
    # return rtcurve_fig

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
# -------------- PREDICTIVE MODEL HELPER FUNCTIONS --------------

def predicted_dates(province_name, region_name, start_date, end_date, days_to_forecast):
    base = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    add_dates = [base + datetime.timedelta(days=x) for x in range(days_to_forecast * 30)]

    for i in range(len(add_dates)):
        add_dates[i] = datetime.datetime.strptime(str(add_dates[i]), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
    
    return add_dates

def predicted_deaths(province_name, region_name, start_date, end_date, days_to_forecast, df_mobility, xMob_slider, facemask_val, vac_val, df_vac):
    base = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    add_dates = [base + datetime.timedelta(days=x) for x in range(days_to_forecast * 30)]
    yVals = []
    lambda_values = [] 
    global total_deaths

    set_total_deaths(province_name, region_name, start_date, end_date)
    last_mort = get_last_mort(province_name, region_name, start_date, end_date)

    total_population = get_total_pop(province_name, region_name)
    annDeath = get_ann_death(province_name, region_name)
    tau = 25.1009
    lS0 = -2.70768
    trend1=-0.0311442
    tmin2 = 24.6497
    dT2 = 0.00562779
    dT3 = 0.000182757
    h0 = 2.30833
    h2 = 5.89094
    anl = -0.007345
    xHouse = get_avg_house(province_name, region_name) # Average number of people/household
    house2 = 0.0198985
    mob1 = 0.0379239
    v2 = 0.0 
    v1 = 11.9697
    xLogPWPD = math.log(get_pwpd(province_name, region_name) * get_frac_pop_over_80(province_name, region_name), 10) # Log10[PWD*AgreFrac[>80]] -> base 10
    xBeta = math.log(total_population / (get_pwpd(province_name, region_name) * get_land_area(province_name, region_name))) / math.log(0.25**2/get_land_area(province_name, region_name)) #get_total_pop(province_name, region_name) / get_land_area(province_name, region_name) # Population Sparsity
    vax2 = 0.0
    first = True
    deaths_tomorrow = 0.0
    deaths_today = last_mort
    total_deaths_2_months_prior = get_total_deaths_2_months_prior(province_name, region_name, end_date)

    for i in range(len(add_dates)):
        date_in_forecast = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=i)
        xAnnual = math.log(annDeath, 10)
        if (first == False):
            xHerd = total_deaths / annDeath  #Total Covid Death/Annual Death -> Annual death as in 2021
            xTrends1 = get_trends_on_day(province_name, region_name, date_in_forecast, facemask_val) # todo: Google Trends for face mask
            xMob1 = get_mob_on_day(date_in_forecast, xMob_slider, 14)
            xMob2 = get_mob_on_day(date_in_forecast, xMob_slider, 28)
            xTemp = get_past_temp(province_name, region_name, date_in_forecast)
            vaxP1 = get_vac_on_day(date_in_forecast, vac_val, total_population, df_vac, 14)
            vaxP2 = get_vac_on_day(date_in_forecast, vac_val, total_population, df_vac, 28)
            # print("vax1: " + str(vaxP1))
            # print("vax2: " + str(vaxP2))

            if (i <= 60):
                xHerd2 = total_deaths_2_months_prior / annDeath # Total Covid Death (more than 2 months ago)/Annual Death -> what does more than 2 months ago mean? 2 months prior
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
            # lambda_ = math.exp(0.5*(lS0 + math.log(10.0)*xLogPWPD + math.log(0.25) +
            #         2.0 / (4.0 - xBeta) * math.log((2.0 - xBeta / 2.0)/(2.0 * 10**xLogPWPD * 0.25**2.0)) - 
            #         h0 * xHerd - h2 * (xHerd - xHerd2) * 6.0 - v1*vax1 + mob1*xMob + 
            #         trend1 * xTrends1 * 1.25 + dT2*(xTemp - tmin2)**2.0 + dT3*(xTemp - tmin2)**3.0 -
            #         math.log(tau))) - 1.0 / tau + house2 * (xHouse - 2.75) + anl * (xAnnual - 3.65) - v2*vax2

            # print("\n logging: " + str(1 - 0.9 * vaxP2) + "\n")
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

    return yVals, lambda_values

def predicted_cases(province_name, region_name, start_date, end_date, days_to_forecast, df_mobility, xMob_slider, facemask_val, vac_val):
    print("todo")

# -------------- MORTALITY HELPER FUNCTIONS --------------

def get_last_mort(province_name, region_name, start_date, end_date):
    start_date_str = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%m-%d-%Y')
    end_date_str = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%m-%d-%Y')

    filtered_df2 = df_mort[df_mort.date_death_report.between(
        start_date_str, end_date_str
    )]
    df_province = filtered_df2[filtered_df2.province == province_name]
    rolling_avgs = df_province.deaths[df_province.health_region == region_name].rolling(window=7).mean()
    rolling_avgs_2 = (df_province.deaths[df_province.health_region == region_name]**2).rolling(window=7).mean()

    vals1 = []
    vals2 = []
    # rolling_avgs_2 = []
    for key in rolling_avgs:
        vals1.append(key)
    for key in rolling_avgs_2:
        vals2.append(key)

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
    deaths = df_province.deaths[df_province.health_region == region_name]

    global total_deaths
    total_deaths = 0 # reset total deaths

    for d in deaths:
        total_deaths += d

    vals1 = []
    for key in rolling_avgs:
        vals1.append(key)

    # global last_mort
    # last_mort = vals1[-1]
    
    return vals1

def get_total_deaths_2_months_prior(province_name, region_name, end_date):
    date_up_to = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    first_day = df_mort.date_death_report.min().date().strftime('%d-%m-%Y')

    delta_2_months = datetime.timedelta(days=60)
    end_date_2_months_ago = date_up_to - delta_2_months
    end_date_2_months_ago = end_date_2_months_ago.strftime('%d-%m-%Y')

    df_2_months = df_mort[df_mort.date_death_report.between(
        first_day, end_date_2_months_ago
    )]
    df_province_2_months = df_2_months[df_2_months.province == province_name]
    deaths_2_months = df_province_2_months.deaths[df_province_2_months.health_region == region_name]

    total_deaths_2_months = 0 # reset total deaths

    for d in deaths_2_months:
        total_deaths_2_months += d

    return total_deaths_2_months

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

def set_total_deaths(province_name, region_name, start_date, end_date):
    start_date_str = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_str = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')

    filtered_df2 = df_mort[df_mort.date_death_report.between(
        start_date_str, end_date_str
    )]
    df_province = filtered_df2[filtered_df2.province == province_name]
    
    deaths = df_province.deaths[df_province.health_region == region_name]

    global total_deaths
    total_deaths = 0 # reset total deaths

    for d in deaths:
        total_deaths += d


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
    # global last_cases
    # last_cases = cases[-1]

    return cases

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

def get_mob_on_day(day, xMob, days_prior):
    first_date_str = df_mobility['date'].iloc[0]
    first_date = datetime.datetime.strptime(first_date_str, "%Y-%m-%d").date()
    
    days_since_first_day = day.date() - first_date - datetime.timedelta(days=days_prior)
    delta = days_since_first_day.days - 1 - 5 # todo: remove -5

    if (delta < len(df_mobility) and delta >= 0):
        mob = df_mobility['workplaces_percent_change_from_baseline'].iloc[delta]
    else:
        mob = xMob
    # print("RETURNING MOB: " + str(mob) + " for day:" + str(day) + " with days prior= " + str(days_prior)) 
    return mob

def get_last_mob():
    total_mob_records = len(df_mobility) - 1
    today_mob = df_mobility['workplaces_percent_change_from_baseline'].iloc[total_mob_records]
    last_mob = -today_mob
    # print("returning mob.... " + str(last_mob))
    return last_mob

def get_mob(province_name, region_name):
    weat_info_province = static_data[static_data.province_name == province_name]
    sub_region = weat_info_province.sub_region_2[weat_info_province.health_region == region_name].item()
    mobs = mobility_info[mobility_info.sub_region_2 == sub_region]
    filtered = mobs[['date', 'workplaces_percent_change_from_baseline']]
    return filtered

# -------------- WEATHER HELPER FUNCTIONS --------------

def get_temp_dates(temp_files):
    dates = []
    for file in temp_files:
        weat_data =  pd.read_csv(file, encoding='Latin-1')
        temp_dates = weat_data['Date/Time'].values
        dates.extend(temp_dates)

    return dates

def get_temp_vals(temp_files):
    temps = []
    # temps = np.arange(10)
    for file in temp_files:
        weat_data =  pd.read_csv(file, encoding='Latin-1')
        temp_dates = weat_data['Mean Temp (°C)'].values
        temps.extend(temp_dates)
    return temps

def get_temp_files(province_name, region, start_date, end_date):
    date_now_str = datetime.datetime.now().strftime('%Y-%m')

    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    num_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
    temp_files = []

    prov_id = provinceid(province_name, region)
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

# def get_temp_files(province_name, region_name, start_date, end_date):

#     start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
#     end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
#     # num_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
#     temp_files = []

#     prov_id = provinceid(province_name, region_name)
#     climate_id = climateid(province_name, region_name)

#     for year in range(start_date.year, end_date.year+1):
#         year = str(year)
#         for month in range(1,13):
#             if month in range(1,10):
#                 month = '0' + str(month)
#             else:
#                 month = str(month)

#             gloabl_date = str(year) + "-" + month
#             target_url = weather_base_url + prov_id + '/climate_daily_' + prov_id + '_' + climate_id + '_' + gloabl_date + '_P1D.csv'
#             temp_files.append(target_url)

#     return temp_files

# Gets the climate ID for the health region
def climateid(province_name, region_name):
    # filtered_df = mobility_info[mobility_info.date.between(
    #     start_date, end_date
    # )]

    weat_info_province = static_data[static_data.province_name == province_name]
    return weat_info_province.climate_id[weat_info_province.health_region == region_name].item()

# Gets the province abbreviation for the health region
def provinceid(province_name, region_name):
    weat_info_province = static_data[static_data.province_name == province_name]
    return weat_info_province.prov_id[weat_info_province.health_region == region_name].item()

def avg_temp_data(begin_year, end_year, data):
    global avg_temp_vals
    df_weat = pd.DataFrame(data, columns = ['Date','Mean Temperature'])
    one_day = datetime.timedelta(days=1)

    next_day = begin_year
    for day in range(0, 366):  # Includes leap year
        if next_day > end_year:
            break
        # Adds a day to the current date
        next_day += one_day
        date_range = next_day.strftime('%m-%d')
        df_weat_date = df_weat.groupby('Date')['Mean Temperature'].mean()

    print("size of df_weat_date: " + str(len(df_weat_date)))
    for val in df_weat_date:
        avg_temp_vals.append(val)
        # print("VAL_: " + str(val))

    print("size of avg_temp_vals: " + str(len(avg_temp_vals)))
    
    return df_weat_date.rolling(window=14).mean()

def get_past_temp(province_name, region_name, day):
    return 0.0
    # print("Size of avg_temp_vals: " + str(len(avg_temp_vals)))
    # day_as_date = day.date()
    # year = str(day_as_date.year)
    # first_day_of_year = year + "-01-01"
    # first_date = datetime.datetime.strptime(first_day_of_year, "%Y-%m-%d").date()
    # days_since_first_day = day.date() - first_date
    # delta = days_since_first_day.days
    # if (delta < len(avg_temp_vals) and delta >= 0):
    #     temp = avg_temp_vals[delta]
    # else:
    #     temp = 0.0
    # # print("returning temp " + str(temp) + " for day: " + str(day))
    # return temp


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
    # print("last vac: " + str(last_vac))

    return last_vac

def get_vac_on_day(date_in_forecast, vac_val, total_population, df_vac, days_prior):
    vac_vals = []

    found_first_day = False
    for day in df_vac:
        if (found_first_day == False and day["total_vaccinations"] != None):
            first_day_vac_str = day["date"]
            found_first_day = True
        elif (day["total_vaccinations"] != None):
            vaccine = day['total_vaccinations']
            vac_vals.append(vaccine)

    first_day_vac_date = datetime.datetime.strptime(first_day_vac_str, '%Y-%m-%d')
    days_since_first_day = date_in_forecast.date() - first_day_vac_date.date() - datetime.timedelta(days=days_prior)
    delta = days_since_first_day.days

    if (delta < len(vac_vals) and delta >= 0):
        vac = vac_vals[delta] / total_population
    elif (delta < 0):
        vac = 0.0
    else:
        vac = vac_val
    
    # print("returning vac on " + str(date_in_forecast) + " == " + str(vac) + " delta is: " + str(delta))
    
    return vac

def vac_df_data(province_name, region_name):
    vac_data = {'date':  get_vaccination_dates(province_name, region_name),
        'total_vaccinations': get_vaccination_vals(province_name, region_name)}
    return vac_data

def vaccination_data(province_name, region_name):
    vac_base_url = "https://api.covid19tracker.ca/reports/regions/"
    vac_base_url_prov = "https://api.covid19tracker.ca/reports/province/"

    if (province_name == 'Alberta') or (province_name == 'New Brunswick') or (province_name == 'NL') or (province_name == 'Nova Scotia'):
        api = vac_base_url_prov + str(provinceid(province_name, region_name))   
    else:
        api = vac_base_url + str(get_uid(province_name, region_name))   
    
    response = requests.get(api)
    api_data = response.json()["data"] 

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
    # print("returning trends: " + str(df_dates[len(df_trends.index) - 1]))
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
    	
    #date_D14 = datetime.datetime.today()	
    #date_D14_t5 = datetime.datetime.today() - datetime.timedelta(days=4)	
    	
    # These should be using the current date but I only have mortality data up till the 14th, hence that being the final date	
    date_D14 = datetime.datetime.strptime("2021-04-14", "%Y-%m-%d")	
    date_D14_t5 = datetime.datetime.strptime("2021-04-14", "%Y-%m-%d") - datetime.timedelta(days=4)	
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
        	
        #print('deaths from a time t:' + str(D14) + ' date:' + str(date_range))	
    	
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
        	
        #print('deaths from a time t five days ago:' + str(D14_t5) + ' date:' + str(date_range))	
   	
    #print(D14_values)	
    #print(D14_t5_values)	
    	
    D14_values = [x+0.5 for x in D14_values]	
    D14_t5_values = [x+0.5 for x in D14_t5_values]    	
    	
    past_data = [x / y if y != 0 else 0.0 for x, y in zip(D14_values, D14_t5_values)]	
    	
    past_data = np.clip(past_data, -3, 10)	
    #print(past_data)	
        	
    return past_data 	

def moving_avg(x, n):	
    cumsum = np.cumsum(np.insert(x, 0, 0)) 	
    return (cumsum[n:] - cumsum[:-n]) / float(n)

if __name__ == "__main__":
    app.run_server(debug=True)
