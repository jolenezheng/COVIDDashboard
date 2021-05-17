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
import dash.dependencies as ddp
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from textwrap import dedent
from dateutil.relativedelta import relativedelta
from pages import *
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

#=================================================
#=========  App/Server Initialization  ===========
#=================================================
external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, external_stylesheets])
server = app.server
app.title = "MyLocalCOVID Portal"


#=========================================
#==========  Data locations  =============
#=========================================

#============ COVID cases and mortality ===========
#
#===BPH-FIXME These data files should be downloaded with cron jobs
#
# Mortality data for all health regions
#   https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_hr/mortality_timeseries_hr.csv
df_mort_all = pd.read_csv(r'data/mortality.csv') 
df_mort_all["date_death_report"] = \
    pd.to_datetime(df_mort_all["date_death_report"], format="%d-%m-%Y") 
# Case data for all health regions
#   https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_hr/cases_timeseries_hr.csv
df_cases_all = pd.read_csv(r'data/cases.csv') 
df_cases_all["date_report"] = \
    pd.to_datetime(df_cases_all["date_report"], format="%d-%m-%Y")

#============ Mobility data ===========
df_mob_all = pd.read_csv(r'data/mobility.csv')
df_mob_all["date"] = \
    pd.to_datetime(df_mob_all["date"], format="%Y-%m-%d") 
#===BPH-FIXME does this do anything?
#df_mob_all["sub_region_2"] = df_mob_all["sub_region_2"]

#============ Google Trends (facemask) data ===========
df_trends_all = pd.read_csv(r'data/google_trends_face_mask_canada.csv')
df_trends_all["date"] = \
    pd.to_datetime(df_trends_all["date"], format="%Y-%m-%d") 

#============ Weather data ===========
weather_data_dir = "data/weather/all_health_regions_actual_avg_temperature_files/2020-01-01_2023-01-01/"

#============ Vaccination data ===========
vac_base_url = "https://api.covid19tracker.ca/reports/regions/"
vac_base_url_prov = "https://api.covid19tracker.ca/reports/province/"

#============ Static data on Health Regions ===========
static_data = pd.read_csv(r'data/health_regions_static_data.csv', encoding='Latin-1')


#===================================================
#===========   Misc Global parameters   ============
#===================================================

pd.set_option('display.max_rows', None)


#=== Number of D(t) and R(t) simulations (Set to 10, unless testing)
default_number_of_simulations = 5

#=== Simulation options
#
# initial value types:
#
#  'use_7day_rollingavg' : 7-day rolling average up to forecast start
#                          (exactly matches plotted "D7" mortality)
#                          (zero values lead to zero predicted deaths)
#
#         'log_smoothed' : interpolate the log of thd "D7" mortality
#                          and do a 14d centered smoothing
#                          (shifts forecast startdate back by a week)
#                          (can estimate correct IC for zero values)
#
simulation_initial_value_type = 'log_smoothed' # 'log_smoothed' 'use_7day_avg'
        
#=== Assumed serial interval (in days) for calculation of
#    Basic Reproduction Number, R(t)
Rt_serial_interval = 5.3 # "tau"
Rt_make_D14_nonzero_offset = 0.5/14.0  # avoid divide-by-zero issue
# Find the 14-day rolling average of the numerical derivative
# lambda_14 before finding R = exp(tau*lambda), or just
# exponentiate and then find the 14-day rolling average of R(t).
Rt_smooth_lambda14_first = True

#== Turn the navbar on/off
navbar_on = True

#=== Plot the temperature as a rolling average (or raw)
plot_weather_14d_rolling = True

#===BPH-FIXME  This global stuff for FAQ should be removed and FAQs fixed
prev_states = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]

#=== Annual death value is from 1997.  Both population and health regions
#    have changed since then.  For now, we just multiply the annual
#    death value by this number
#===BPH-FIXME: really should have a health-region dependent factor
population_factor_1997_to_today = 1.3

# Fraction of total vaccinations with one-dose vaccines
frac_vax_one_dose = 0.115

# The searches for "face mask" are much lower in french-speaking QC, so:
trends_mult_factor_for_QC = 2.5

# When doing predictive model, if data is missing return this
#  (then the assumed value is given by the slider value)
no_data_val = 999999

# Maximum fraction assumed vaccinated
maximum_fraction_vaccinated = 0.9
# Maximum effectiveness of vaccine (1 = 100%)
maximum_vaccine_effectiveness = 0.9 # 90%

#========================================================
#====    Menu/slider options and initial values    ======
#========================================================
#=== Initially displayed province/region
initial_province = "Ontario"
initial_region = "Toronto"
#=== Initially displayed forecast: show a 12-month forecast starting 10-months ago
nowdate = datetime.datetime.now()
days_in_month = 30 # to be used for forecast length (quoted in months)
forecast_initial_length = 12 # [testing (5days): 1/6.0 , default (1yr): 12]
forecast_initial_start_date = \
    (nowdate - datetime.timedelta(days=10*days_in_month)).strftime("%Y-%m-%d")
#=== Max and min possible dates for plotting range
first_mortality_date = df_mort_all.date_death_report.min()
first_mortality_date_str = first_mortality_date.strftime("%Y-%m-%d")
last_mortality_date = df_mort_all.date_death_report.max()
last_mortality_date_str = last_mortality_date.strftime("%Y-%m-%d")
first_possible_date=datetime.datetime.strptime("2020-01-01", "%Y-%m-%d")
last_possible_date = datetime.datetime.strptime("2023-01-01", "%Y-%m-%d")
#=== Set initial slider values to negative, so that initial
#    runs of graphs will get updated values for the region
initial_nonvalue = -9999
initial_facemask_slider = initial_nonvalue
initial_mobility_slider = initial_nonvalue
initial_vaccine_slider = initial_nonvalue

#===========================================================
#=========  Plotly Graph Options (all graphs)  =============
#===========================================================

plotly_template = pio.templates["plotly_dark"]

graph_background_color = "LightSteelBlue" # None "LightSteelBlue"
graph_plot_color = "#e5ecf6" # None "lightgrey" "#e5ecf6"
graph_margins = dict(l=80, r=20, t=20, b=20)

buttons_annotations = [
    dict(text="Vertical Axis Scale:", x=0.8, xref="paper", y=1.15, yref="paper",
         align="right", showarrow=False),
    ]

buttons_updatemenus = [
        dict(
            type="buttons",
            xanchor="right",
            yanchor="top",
            direction="right",
            #pad={"r": 1, "t": 1},
            x=1,
            y=1.18,
            buttons=list([
                dict(
                    args=[{'yaxis.type': 'linear'}],
                    label="Linear",
                    method="relayout"
                ),
                dict(
                    args=[{'yaxis.type': 'log'}],
                    label="Log",
                    method="relayout"
                )
            ])
        ),
    ]


#==================================================
#=======   Province/region info for menu    =======
#==================================================
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
all_province_names = list(fnameDict.keys())
nestedOptions = fnameDict[all_province_names[0]]

#====================================================
#===========   Dashboard HTML Content   =============
#====================================================

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


footer2 = html.Footer(html.Div([
    "Dashboard made by Jolene Zheng and Shafika Olalekan Koiki | ",
    html.A(" GitHub", href="https://github.com/jolenezheng/COVIDDashboard/", target="_blank")
], className="footer"))

if navbar_on:
    site_backbone = html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(navbar2),
        html.Div(id='page-content', className="page border"),
        footer2,
    ])
else:
    site_backbone = html.Div([
        dcc.Location(id='url', refresh=False),
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
                                                    options=[{'label':name, 'value':name} for name in all_province_names],
                                                    value = initial_province
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
                                                    value = initial_region
                                                ),
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            children=[
                                                html.Div(
                                                    children="Number of Simulations",
                                                    className="dropdown-title"
                                                    ),
                                                 dcc.Input(
                                                     id="number-of-simulations",
                                                     type="number",
                                                     placeholder="input",
                                                     value=default_number_of_simulations,
                                                     min=1,
                                                     max=10,
                                                     step='any',
                                                 ),
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            dbc.Button("Run Forecast", id='rerun-btn1', n_clicks=0,
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
                                                    children="Face Masks: Google Trends",
                                                    className="dropdown-title"
                                                    ),
                                                dcc.Slider(
                                                    id='facemask-slider',
                                                    min=0,
                                                    max=100,
                                                    step=1,
                                                    value=initial_facemask_slider,
                                                    marks={
                                                        0: '0',
                                                        25: '25',
                                                        50: '50',
                                                        75: '75',
                                                        100: '100'
                                                    },
                                                ),
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            children=[
                                                html.Div(
                                                    children="Workplace Mobility Reduction",
                                                    className="dropdown-title"
                                                    ),
                                                dcc.Slider(
                                                    id='mobility-slider',
                                                    min=0,
                                                    max=100,
                                                    step=1,
                                                    value=initial_mobility_slider,
                                                    marks={
                                                        0: '0%',
                                                        20: '20%',
                                                        40: '40%',
                                                        60: '60%',
                                                        80: '80%',
                                                        100: '100% (lockdown)'
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
                                                    value=initial_vaccine_slider,
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
                                                    children="Maximum Vaccination Percent",
                                                    className="dropdown-title"
                                                    ),
                                                 dcc.Input(
                                                     id="max-vaccination-percent",
                                                     type="number",
                                                     placeholder="input",
                                                     value=100*maximum_fraction_vaccinated,
                                                     min=5,
                                                     max=100,
                                                     step='any',
                                                 ),
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            children=[
                                                html.Div(
                                                    children="Date to Start Forecast (mm/dd/yyyy)",
                                                    className="dropdown-title",
                                                    ),
                                                dcc.DatePickerSingle(
                                                    id="forecast-start-date",
                                                    min_date_allowed=first_mortality_date.date(),
                                                    max_date_allowed=last_mortality_date.date(),
                                                    initial_visible_month=last_mortality_date.date(), 
                                                    date=forecast_initial_start_date
                                                ),
                                                html.Div(
                                                    "start date might be set earlier if data is sparse",
                                                    style={'color': 'red', 'fontSize':'x-small'}
                                                    )
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            children=[
                                                html.Div(
                                                    children="Number of Months to Forecast",
                                                    className="dropdown-title"
                                                    ),
                                                dcc.Slider(
                                                    id='forecast-slider',
                                                    min=0,
                                                    max=24,
                                                    step=1.0,
                                                    value=forecast_initial_length, 
                                                    marks={ 0: '0', 4: '4', 8: '8',
                                                        12: '12', 16: '16', 20: '20', 24: '24'
                                                    },
                                                ),
                                            ]
                                        ),
                                    ), className='input-space'),
                                    dbc.Row(dbc.Col(
                                        html.Div(
                                            dbc.Button("Run Forecast", id='rerun-btn2', n_clicks=0,
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
                                        dbc.CardHeader("Workplace Mobility Reduction"),
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
                                    dbc.CardHeader(id="mortality-header"),
                                    dbc.CardBody(
                                         dcc.Loading(
                                            children=[html.Div(dcc.Graph(
                                                id="mortality-chart",
                                                config={"displayModeBar": False}))],
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
                        dbc.Row(
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(id="cumulativedeaths-header"),
                                        dbc.CardBody(
                                            dcc.Loading(
                                                children=[html.Div(dcc.Graph(
                                                    id="cumulativedeaths-chart",
                                                    config={"displayModeBar": False}))],
                                                type="default"
                                            )),
                                        # dbc.CardBody(
                                        #     dcc.Graph(
                                        #         id="cases-chart", config={"displayModeBar": False}, # style={'display': 'inline-block'},
                                        #     ),
                                        # ),
                                    ], color="dark", inverse=True),
                            ), className="mb-4"),                        
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


#=====================================================
#============       App Callbacks        =============
#=====================================================

#=================#
#    Page Load    #
#=================#
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

#=================#
#     FAQ Page    #
#=================#
#===BPH-FIXME FAQ needs fixin
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

#========================================================#
#   Region --> Get Health Region options (Sub-Region)    #
#========================================================#
@app.callback(
    ddp.Output('subregion-dropdown', 'options'),
    ddp.Input('region-dropdown', 'value'),
)
def update_subregion_dropdown(province):
    print("START --- update_subregion_dropdown \t", nowtime())
    print("END   --- update_subregion_dropdown \t", nowtime())    
    return [{'label': i, 'value': i} for i in fnameDict[province]]

#=================================================================#
#   Rerun/Sub-region -> Set static card values to health region   #
#=================================================================#
@app.callback(
    [
        ddp.Output('total-pop-card', 'children'),
        ddp.Output('sparsity-card', 'children'),
        ddp.Output('frac-pop-card', 'children'),
        ddp.Output('pwpd-card', 'children'),
        ddp.Output('avg-house-card', 'children'),
        ddp.Output('mob-card', 'children'),
    ],
    [
        ddp.Input('subregion-dropdown', 'value')
    ],
    [
        ddp.State('region-dropdown', 'value'),
    ]
)
def update_static_cards(region_name, province_name):

    print("START --- update_static_cards \t\t", nowtime())
    
    province_name = update_province_name(province_name)

    #=== Get 7-day rolling avg of mobility data for this region
    df_mob = get_hr_mob_df(province_name, region_name)
    # and the last value of that rolling average
    last_mob = get_last_val('mob', df_mob)

    #=== Calculate all card values
    mob = f"{-last_mob:.0f} %"
    total_pop = round(get_total_pop(province_name, region_name), 0)
    sparsity = round(get_pop_sparsity(province_name, region_name), 3)
    pop_80 = round(get_frac_pop_over_80(province_name, region_name), 3)
    pwpd = round(get_pwpd(province_name, region_name), 0)
    avg_house = round(get_avg_house(province_name, region_name), 2)

    # todo: sparsity (3 digits)
    # pop_80 = round(get_frac_pop_over_80(province_name, region_name), 2)
    # pwpd = round(get_pwpd(province_name, region_name), 2)

    print("END   --- update_static_cards \t\t", nowtime())
    
    return total_pop, sparsity, pop_80, pwpd, avg_house, mob

#===================================================================#
#   Rerun/Sub-region --> Set dynamic card values for health region  #
#===================================================================#
@app.callback(
    [
        ddp.Output('covid-deaths-card', 'children'),
        ddp.Output('cases-card', 'children'),
        ddp.Output('covid-deaths2-card', 'children'),
    ],
    [
        ddp.Input('subregion-dropdown', 'value'),
    ],
    [
        ddp.State('region-dropdown', 'value'),
    ]
)
def update_dynamic_cards(region_name, province_name):

    print("START --- update_dynamic_cards \t\t", nowtime())

    province_name = update_province_name(province_name)
    total_pop = get_total_pop(province_name, region_name)

    #=== Get COVID-19 mortality for all dates
    df_mort = get_hr_mortality_df(province_name, region_name)
    total_covid_deaths = df_mort.deaths.sum()

    #=== Get the (1997-growth-adjusted) annual death
    annual_deaths = get_annual_death(province_name, region_name)

    #===BPH annual-covid-deaths should be over a one-year period
    today = datetime.datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    lastyear_today = (today - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    annual_covid_deaths = \
        df_mort[df_mort.date_death_report.between(lastyear_today, today_str)]['deaths'].sum()
    covid_per_annual = str(round(annual_covid_deaths / annual_deaths * 100.0, 3)) + "%"
    deaths_per_pop = str(round(total_covid_deaths / total_pop * 100.0, 3)) + "%"

    #=== Get all cases
    cases_df = get_hr_cases_df(province_name, region_name)
    total_cases = cases_df.cases.sum()
    cases_per_pop = str(round(total_cases / total_pop * 100.0, 3)) + "%"

    print("END   --- update_dynamic_cards \t\t", nowtime())

    return deaths_per_pop, cases_per_pop, covid_per_annual

#======================================================#
#   Rerun -> Set graph headers                         #
#======================================================#
@app.callback(
    [
        ddp.Output("mortality-header", "children"),
        ddp.Output("cases-header", "children"),
        ddp.Output("mob-header", "children"),
        ddp.Output("temp-header", "children"),
        ddp.Output("vac-header", "children"),
        ddp.Output("trends-header", "children"),
        ddp.Output("rtcurve-header", "children"),
        ddp.Output("cumulativedeaths-header", "children")
    ],
    [
        ddp.Input('subregion-dropdown', 'value')        
    ],
    [
        ddp.State('region-dropdown', 'value'),
    ]
)
def update_headers(region_name, province_name):

    print("START --- update_static_cards \t\t", nowtime())
    
    province_name = update_province_name(province_name)

    # Graph Titles
    deaths_label = 'Daily Deaths in ' + region_name + ', ' + province_name 
    cases_label = 'Daily Reported Cases in ' + region_name + ', ' + province_name \
        + " (not used for forecasting)"
    mob_label = 'Workplace Social Mobility in ' + region_name + ', ' + province_name
    temp_label = 'Daily Reported Temperature in ' + region_name + ', ' + province_name
    vac_label = 'Vaccination of Population in ' + region_name + ', ' + province_name
    trends_label = 'Google Searches for Face Masks in ' + region_name + ', ' + province_name
    rtcurve_label = 'Effective Reproduction Number R(t) Curves for ' + region_name + ', ' \
        + province_name + " (black = actual, colors = predicted)"
    cumulativedeaths_label = 'Cumulative Deaths in ' + region_name + ', ' + province_name

    print("END   --- update_static_cards \t\t", nowtime())
    
    return [deaths_label, cases_label, mob_label, temp_label, vac_label,
            trends_label, rtcurve_label, cumulativedeaths_label]

#==================================================#
#  Sub-Region --> Set slider values for sub-region #
#==================================================#
@app.callback(
    [
        ddp.Output("facemask-slider", "value"),
        ddp.Output("mobility-slider", "value"),
        ddp.Output("vaccine-slider", "value"),
    ],
    [
        ddp.Input('subregion-dropdown', 'value')
    ],
    [  
        ddp.State('region-dropdown', 'value'), 
    ]
)
def set_slider_vals(region_name, province_name):

    print("START --- set_slider_vals \t\t", nowtime())
    
    province_name = update_province_name(province_name)

    last_trends, last_mob, vax_rate_percent = \
        get_last_trends_mob_vaxrate_for_region(province_name, region_name)
    
    print("END   --- set_slider_vals \t\t", nowtime())
    
    return last_trends, last_mob, vax_rate_percent

#========================================================#
#   Rerun --> Get Cases Graph                            #
#========================================================#
@app.callback(
    ddp.Output("cases-chart", "figure"), 
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks'),
        ddp.Input("subregion-dropdown", "value")        
    ],
    [
        ddp.State("region-dropdown", "value"),
        ddp.State("forecast-start-date", "date"),
        ddp.State('forecast-slider', 'value'),        
    ],
)
def update_cases_charts(n_clicks1, n_clicks2, region_name, province_name, 
                        day_to_start_forecast, months_to_forecast):
    print("START --- update_cases_chart \t\t", nowtime())

    daterange = get_daterange(day_to_start_forecast, months_to_forecast)

    province_name = update_province_name(province_name)

    df_cases = get_hr_cases_df(province_name, region_name).copy()
    df_cases = df_cases[df_cases.date_report.between(daterange[0], daterange[1])]

    df_cases['cases'] = df_cases['cases'].rolling(window=7).mean()


    #===BPH For some reason this works for weather, but not here.  I get an error:
    #
    #       ValueError: Invalid value
    #     
    # cases_fig = px.line(df_cases, x = 'date_report', y = 'cases')
    #
    # Luckily this works just fine:
    cases_fig = go.Figure()
    cases_fig.add_trace(
        go.Scatter(
            x=df_cases['date_report'], y=df_cases['cases'],
            name='Previous Cases', line=dict(color='black', width=2)
        )
    )
    cases_fig.update_layout(xaxis_title='Date',
                            yaxis_title='Daily Cases (7-day rolling avg)',
                            paper_bgcolor = graph_background_color,
                            plot_bgcolor = graph_plot_color,                           
                            margin = graph_margins,
                            xaxis_range = daterange,
                            showlegend=False,                           
                            annotations=buttons_annotations,
                            updatemenus=buttons_updatemenus,
                            )
    
    print("END   --- update_cases_chart \t\t", nowtime())    

    return cases_fig

#========================================================#
#   Rerun --> Get Mortality Graph with Simulations       #
#         --> Get R(t) Graph with Simulations            #
#========================================================#
@app.callback(
    [
        ddp.Output("mortality-chart", "figure"),
        ddp.Output("rtcurve-chart", "figure")
    ],
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks'),
        ddp.Input("subregion-dropdown", "value"),
    ],
    [
        ddp.State("region-dropdown", "value"),
        ddp.State("forecast-start-date", "date"),
        ddp.State('forecast-slider', 'value'),
        ddp.State('facemask-slider', 'value'),
        ddp.State('mobility-slider', 'value'),
        ddp.State('vaccine-slider', 'value'),
        ddp.State('max-vaccination-percent', 'value'),
        ddp.State('number-of-simulations', 'value'),
    ],
)
def update_mortality_chart(n_clicks1, n_clicks2, region_name, province_name, 
                           day_to_start_forecast, months_to_forecast,
                           facemask_slider, mob_slider,
                           vac_slider, max_vax_percent, n_simulations):    
    
    print("START --- update_mortality_chart \t", nowtime())
    
    province_name = update_province_name(province_name)
    
    #=== Check to see if a button was clicked (do simulations)
    #    or if just the region was changed (replot data only)
    #          https://stackoverflow.com/questions/62671226
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if ( ('rerun-btn1' in changed_id) | ('rerun-btn2' in changed_id) ):
        do_simulations = True
    else:
        do_simulations = False
    if ('subregion-dropdown' in changed_id):
        subregion_changed = True
    else:
        subregion_changed = False
    #=== Identify an initial run or an update for the region
    #    and set slider values manually
    if ( (mob_slider == initial_nonvalue)
         | (facemask_slider == initial_nonvalue)
         | (vac_slider == initial_nonvalue)
         | (subregion_changed) ):
        facemask_slider, mob_slider, vac_slider = \
            get_last_trends_mob_vaxrate_for_region(province_name, region_name)
    
    print("      --- update_mortality_chart \t", nowtime(), " --- slider data loaded")
    
    #=== Set the daterange (same for all graphs).  This is currently:
    #         [first_mortality_date, forecast_startdate + forecast_length]
    daterange = get_daterange(day_to_start_forecast, months_to_forecast)
    
    #=== Adjust slider values for use in model forecast
    mob_slider_negative = -1*mob_slider
    vac_slider_fraction = vac_slider / 100.0
    max_vax_fraction = max_vax_percent / 100
    
    #=== Get the mortality dataframe and make a copy for plotting
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    df_mort = get_hr_mortality_df(province_name, region_name, getall=False,
                                  startdate=daterange[0], enddate=today_str)
    df_mort_plot = df_mort.copy()
    df_mort_plot['deaths'] = df_mort_plot['deaths'].rolling(window=7).mean()
    
    print("      --- update_mortality_chart \t", nowtime(), " --- mortality loaded")
    print("      --- update_mortality_chart \t", nowtime(), " --- started plotting deaths")
    
    #=== Initialize mortality figure and plot the actual (7d-avg) mortality
    mortality_fig = go.Figure()
    mortality_fig.add_trace(
        go.Scatter(
            x=df_mort_plot['date_death_report'],
            y=df_mort_plot['deaths'],
            name='Previous Deaths',
            line=dict(color='black', width=2)
        )
    )

    #=== Some optional plotting for testing
    testing_logsmoothed = False
    if testing_logsmoothed:
        df_mort_plot2 = df_mort[['date_death_report', 'deaths']].copy()
        df_mort_plot2['deaths'] = df_mort_plot2['deaths'].rolling(window=7).mean()        
        df_mort_plot2['logdeaths'] = 0.0
        for index, row in df_mort_plot2.iterrows():
            if row.deaths == 0.0:
                df_mort_plot2.at[index, 'logdeaths'] = np.nan
            else:
                df_mort_plot2.at[index, 'logdeaths'] = np.log(row.deaths)
        #df_mort_plot2['logdeaths'] = \
        #    df_mort_plot2['logdeaths'].rolling(window=14).mean()
        df_mort_plot2['logdeaths'] = \
            df_mort_plot2['logdeaths'].rolling(window=14, center=True).mean()
        df_mort_plot2['logdeaths'] = \
            df_mort_plot2['logdeaths'].interpolate(method='polynomial', order=2)
        df_mort_plot2['deaths'] = np.exp(df_mort_plot2['logdeaths'])

        mortality_fig.add_trace(
            go.Scatter(
                x=df_mort_plot2['date_death_report'],
                y=df_mort_plot2['deaths'],
                name='Previous Deaths',
                mode='lines',
                line={'dash': 'dash', 'color' : 'red'}
            )
        )
        
    
    print("      --- update_mortality_chart \t", nowtime(), " --- finished plotting deaths")
    print("      --- update_mortality_chart \t", nowtime(), " --- started plotting R(t)")
    

    #=== Calculate R(t) from mortality data
    df_mort_Rt = calculate_Rt_from_mortality(df_mort)
    
    #=== Initialize R(t) figure and plot the R(t) from actual mortality data
    rtcurve_fig = go.Figure()
    rtcurve_fig.add_trace(
        go.Scatter(
            x=df_mort_Rt['date_death_report'],
            y=df_mort_Rt['Rt'],
            name='Reproduction Number',
            line=dict(color='black', width=2)
        )
    )
    print("      --- update_mortality_chart \t", nowtime(), " --- finished plotting R(t)")
    
    if do_simulations:

        #=== Load other data ===
        print("      --- update_mortality_chart \t", nowtime(), " --- started loading data")
        # Get "fraction_vaccinated" dataframe
        df_vac = get_hr_vac_data(province_name, region_name)
        last_vax_fraction = get_last_val('vac', df_vac)
        print("      --- update_mortality_chart \t", nowtime(), " --- vaccination loaded")    
        # Get the 7-day rolling average of the mobility data
        df_mobility = get_hr_mob_df(province_name, region_name)
        print("      --- update_mortality_chart \t", nowtime(), " --- mobility loaded")
        #=== Get weather dataframe
        df_weather = get_weather_dataframe(province_name, region_name)
        print("      --- update_mortality_chart \t", nowtime(), " --- weather loaded")
        #=== Get the 7-day rolling average of Google trends for "facemasks"
        #   (also w/ tanh mask applied about 15Apr2020)
        df_trends = get_hr_trends_df(province_name, region_name)
        print("      --- update_mortality_chart \t", nowtime(), " --- trends loaded")    
        print("      --- update_mortality_chart \t", nowtime(), " --- finished loading data")

    
        #=== Run forecast simulations
        for i in range(n_simulations):
            print("      --- update_mortality_chart \t", nowtime(), " --- D(t) CURVE: " + str(i))
            df_forecast, new_forecast_startdate, df_mort_logsmooth = \
                get_forecasted_mortality(province_name, region_name,
                                         day_to_start_forecast, months_to_forecast,
                                         df_mort, df_mobility, df_vac, df_weather, df_trends,
                                         mob_slider_negative,
                                         vac_slider_fraction, last_vax_fraction,
                                         max_vax_fraction,
                                         facemask_slider)
            df_forecast = \
                df_forecast[df_forecast.date.between(new_forecast_startdate, daterange[1])]
            #=== Add simulated forecast of mortality to the mortality figure
            mortality_fig.add_trace(
                go.Scatter(
                    x=df_forecast['date'],
                    y=df_forecast['deaths'],
                    mode = 'lines',
                    name='Prediction ' + str(i+1),
                )
            )
            #=== Add log-smoothed mortality pre-forecast to show 
            #    selection of potentially new forecast startdate
            if (df_mort_logsmooth is not None):
                mortality_fig.add_trace(
                    go.Scatter(
                        x=df_mort_logsmooth['date'],
                        y=df_mort_logsmooth['deaths'],
                        name='Previous Deaths',
                        mode='lines',
                        line={'dash': 'dash', 'color' : 'red'}
                    )
                )
            #=== Add simulated forecast of R(t) to the R(t) figure
            df_forecast['R(t)'] = \
                np.exp( Rt_serial_interval * df_forecast['lambda'] )
            # take moving average
            df_forecast['R(t)'] = df_forecast['R(t)'].rolling(window=14).mean()            
            rtcurve_fig.add_trace(
                go.Scatter(
                    x = df_forecast['date'].to_list(),
                    y = df_forecast['R(t)'].to_list(),
                    mode = 'lines',
                    name='Prediction ' + str(i+1),
                )
            )
    print("      --- update_mortality_chart \t", nowtime(), " --- finished simulations")    
    #=== Apply updates to figures
    mortality_fig.update_layout(xaxis_title='Date',
                           yaxis_title='Daily Mortality (7-day rolling avg)',
                           paper_bgcolor = graph_background_color,
                           plot_bgcolor = graph_plot_color,                           
                           margin = graph_margins,
                           xaxis_range = daterange,
                           showlegend=False,                           
                           annotations=buttons_annotations,
                           updatemenus=buttons_updatemenus,
                           )
    rtcurve_fig.update_layout(xaxis_title='Date',
                              yaxis_title='R(t) Curve Based On Mortality',
                              paper_bgcolor = graph_background_color,
                              plot_bgcolor = graph_plot_color,                           
                              margin = graph_margins,
                              xaxis_range = daterange,
                              showlegend=False,                           
                              )
    
    print("END   --- update_mortality_chart \t", nowtime())
    
    return mortality_fig, rtcurve_fig

#========================================================#
#   Rerun --> Get Cumulative Death Graph                 #
#========================================================#
@app.callback(
    ddp.Output("cumulativedeaths-chart", "figure"),
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks'),
        ddp.Input("subregion-dropdown", "value"),
    ],
    [
        ddp.State("region-dropdown", "value"),
        ddp.State("forecast-start-date", "date"),
        ddp.State('forecast-slider', 'value'),
    ],
)
def update_cumulativedeaths_charts(n_clicks1, n_clicks2, region_name, province_name,
                                   day_to_start_forecast, months_to_forecast):
    print("START --- update_cumulativedeath_chart \t", nowtime())
    
    daterange = get_daterange(day_to_start_forecast, months_to_forecast)    

    province_name = update_province_name(province_name)

    start_date = daterange[0]
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    end_date = today_str
    #===BPH-FIXME: redo these using dataframes
    dates = get_dates_list(province_name, region_name, start_date, end_date)
    cumulativedeaths = get_cumulative_deaths(province_name, region_name,
                                             start_date, end_date)
    
    cumulativedeaths_fig = go.Figure()

    cumulativedeaths_fig.add_trace(go.Scatter(
            x=dates,
            y=cumulativedeaths,
            name='Cumulative Deaths',
        ))
    
    cumulativedeaths_fig.update_layout(xaxis_title='Date',
                                       yaxis_title='Number of Deaths',
                                       xaxis_range = daterange,
                                       paper_bgcolor = graph_background_color,
                                       plot_bgcolor = graph_plot_color,                           
                                       margin = graph_margins,
                                       showlegend=False,                           
                                       annotations=buttons_annotations,
                                       updatemenus=buttons_updatemenus,
                                       )

    print("START --- update_cumulativedeath_chart \t", nowtime())
    
    return cumulativedeaths_fig

#========================================================#
#   Rerun --> Get Mobility Graph                         #
#========================================================#
@app.callback(
    ddp.Output("mobility-chart", "figure"),
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks'),
        ddp.Input("subregion-dropdown", "value"),
        ddp.Input('mobility-slider', 'value'),
    ],        
    [
        ddp.State("region-dropdown", "value"),
        ddp.State("forecast-start-date", "date"),
        ddp.State('forecast-slider', 'value'),
    ],
)
def update_mob_charts(n_clicks1, n_clicks2, region_name, mob_slider, province_name, 
                      day_to_start_forecast, months_to_forecast):
    print("START --- update_mob_charts \t\t", nowtime())
    #print("      --- update_mob_charts \t\t", nowtime(), " --- xMob=" + str(xMob))

    daterange = get_daterange(day_to_start_forecast, months_to_forecast)
    
    province_name = update_province_name(province_name)

    #=== Check to see if subregion changed
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if ('subregion-dropdown' in changed_id):
        subregion_changed = True
    else:
        subregion_changed = False
    #=== Identify an initial run or sub-region change
    #    and set slider values manually
    if ( (mob_slider == initial_nonvalue) | (subregion_changed) ):
        facemask_slider, mob_slider, vac_slider = \
            get_last_trends_mob_vaxrate_for_region(province_name, region_name)

    #=== Set value for plotting
    mob_slider_neg = -1.0*mob_slider

    #=== Get the 7-day rolling average of the mobility
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    df_mob = get_hr_mob_df(province_name, region_name, getall=False,
                                  startdate=daterange[0], enddate=today_str)

    #=== Plot the actual Mobility data
    mobility_fig = go.Figure()    
    mobility_fig.add_trace(
        go.Scatter(
            x=df_mob['date'],
            y=df_mob['workplaces_percent_change_from_baseline'],
            name='Actual Mobility',
            mode = 'lines',
        )
    )

    #=== Create and plot a constant mobility function
    start_date = df_mob.date.max()
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date = daterange[1]
    rng = pd.date_range(start_date, end_date)
    df_mob_plot_constant = pd.DataFrame({'date': rng,
                                         'mob': mob_slider_neg * np.ones(len(rng))})
    mobility_fig.add_trace(
        go.Scatter(
            x=df_mob_plot_constant['date'],
            y=df_mob_plot_constant['mob'],
            name='Predicted Mobility',
            mode = 'lines',            
        )
    )
    
    mobility_fig.update_layout(xaxis_title='Date',
                               yaxis_title='Workplace Social Mobility',
                               paper_bgcolor = graph_background_color,
                               plot_bgcolor = graph_plot_color,                           
                               margin = graph_margins,
                               xaxis_range = daterange,
                               showlegend=False,                           
                               )

    print("END   --- update_mob_charts \t\t", nowtime())
    
    return mobility_fig

#========================================================#
#   Rerun --> Get Vaccination Graph                      #
#========================================================#
@app.callback(
    ddp.Output("vac-chart", "figure"),
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks'),
        ddp.Input("subregion-dropdown", "value"),
        ddp.Input('vaccine-slider', 'value'),
        ddp.Input('max-vaccination-percent', 'value'),        
    ],
    [
        ddp.State("region-dropdown", "value"),
        ddp.State("forecast-start-date", "date"),
        ddp.State('forecast-slider', 'value'),
    ],
)
def update_vaccination_charts(n_clicks1, n_clicks2, region_name, vac_slider,
                              max_vax_percent, province_name,
                              day_to_start_forecast, months_to_forecast):
    
    print("START --- update_vaccination_chart \t", nowtime())
    
    daterange = get_daterange(day_to_start_forecast, months_to_forecast)
    
    province_name = update_province_name(province_name)
    
    #=== Check to see if subregion changed
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if ('subregion-dropdown' in changed_id):
        subregion_changed = True
    else:
        subregion_changed = False
    #=== Identify an initial run or a region update
    #    and set slider values manually
    if ( (vac_slider == initial_nonvalue) | (subregion_changed) ):
        facemask_slider, mob_slider, vac_slider = \
            get_last_trends_mob_vaxrate_for_region(province_name, region_name)

    #=== Get fraction_vaccinated dataframe
    df_vac = get_hr_vac_data(province_name, region_name).copy()
    
    #=== Plot the actual fraction_vaccinated data
    vaccination_fig = go.Figure()    
    vaccination_fig.add_trace(
        go.Scatter(
            x=df_vac['date'],
            y=100*df_vac['fraction_vaccinated'],
            name='Estimated Percent Vaccinated',
            mode = 'lines',            
        )
    )
    
    #=== Create and plot the extrapolation of fraction_vaccinated
    #
    # get value and date of last vaccination data
    last_vax_fraction = get_last_val('vac', df_vac)
    start_date_str = df_vac.date.max()
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
    # initialize dataframe of linear extrapolation
    end_date_str = daterange[1]
    rng = pd.date_range(start_date_str, end_date_str)
    df_vax_frac_extrap = pd.DataFrame({'date': rng,
                                  'linear_extrap' : np.zeros(len(rng))})
    # make column with days since last vax data
    df_vax_frac_extrap['days_since_last'] = \
        (df_vax_frac_extrap['date'] - start_date).dt.days
    # calculate the linear extrapolated values
    vax_fraction_per_week = vac_slider / 100.0
    max_vax_fraction = max_vax_percent / 100.0
    df_vax_frac_extrap = \
        get_linear_extrap_vax(last_vax_fraction, vax_fraction_per_week,
                              max_vax_fraction, 'days_since_last',
                              df=df_vax_frac_extrap)
    # plot the extrapolated values
    vaccination_fig.add_trace(
        go.Scatter(
            x=df_vax_frac_extrap['date'],
            y=100*df_vax_frac_extrap['linear_extrap'],
            name='Extrapolated Percent Vaccination',
            mode = 'lines',            
        )
    )
    
    vaccination_fig.update_layout(xaxis_title='Date',
                                  yaxis_title='Estimated Percent Vaccinated',
                                  paper_bgcolor = graph_background_color,
                                  plot_bgcolor = graph_plot_color,                           
                                  margin = graph_margins,
                                  xaxis_range = daterange,
                                  showlegend=False,                           
                                  )
    
    print("END   --- update_vaccination_chart \t", nowtime())
    
    return vaccination_fig

#========================================================#
#   Rerun --> Get Temperature Graph                      #
#========================================================#
@app.callback(
    ddp.Output("weather-chart", "figure"),
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks'), 
        ddp.Input("subregion-dropdown", "value"),
    ],
    [
        ddp.State("region-dropdown", "value"),
        ddp.State("forecast-start-date", "date"),
        ddp.State('forecast-slider', 'value'),
    ],
)
def update_weather_chart(n_clicks1, n_clicks2, region_name, province_name,
                         day_to_start_forecast, months_to_forecast,):
    print("START --- update_weather_chart \t\t", nowtime())

    daterange = get_daterange(day_to_start_forecast, months_to_forecast)

    province_name = update_province_name(province_name)

    # Get weather dataframe
    df_weather = get_weather_dataframe(province_name, region_name)
    # select out current and future data
    today = datetime.datetime.today()
    df_weather = df_weather[df_weather.date.between(daterange[0], daterange[1])].copy()
    if plot_weather_14d_rolling:
        df_weather['temp_mean'] = \
            df_weather['temp_mean'].rolling(window=14).mean()
    df_weather_current = df_weather[df_weather.date < today]
    df_weather_future = df_weather[df_weather.date >= today]    

    weather_fig = px.line(df_weather_current, x = 'date', y = 'temp_mean')

    weather_fig.add_trace(go.Scatter(	
        x = df_weather_future['date'],
        y = df_weather_future['temp_mean'],
        mode = 'lines',
        name='Historical Average',	
    ))
    
    weather_fig.update_layout(xaxis_title='Date',	
                              yaxis_title='Mean Temperature (14-day rolling avg)',
                              paper_bgcolor = graph_background_color,
                              plot_bgcolor = graph_plot_color,                           
                              margin = graph_margins,
                              xaxis_range = daterange,
                              showlegend=False,                           
                              )

    print("END   --- update_weather_chart \t\t", nowtime())
    
    return weather_fig

#========================================================#
#   Rerun --> Get Facemask Google-Trends Graph           #
#========================================================#
@app.callback(
    ddp.Output("trends-chart", "figure"),
    [
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks'),
        ddp.Input("subregion-dropdown", "value"),
        ddp.Input('facemask-slider', 'value'),
    ],
    [
        ddp.State("region-dropdown", "value"),
        ddp.State("forecast-start-date", "date"),
        ddp.State('forecast-slider', 'value'),
    ],
)
def update_trends_charts(n_clicks1, n_clicks2, region_name, facemask_slider,
                         province_name, day_to_start_forecast, months_to_forecast):
    print("START --- update_trends_chart \t\t", nowtime())

    daterange = get_daterange(day_to_start_forecast, months_to_forecast)
    
    province_name = update_province_name(province_name)

    #=== Check to see if subregion changed
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if ('subregion-dropdown' in changed_id):
        subregion_changed = True
    else:
        subregion_changed = False
    #=== Identify an initial run or an update for the region
    #    and set slider values manually
    if ( (facemask_slider == initial_nonvalue) | (subregion_changed) ):
        facemask_slider, mob_slider, vac_slider = \
            get_last_trends_mob_vaxrate_for_region(province_name, region_name)

    # Get 7-day average trends data
    df_trends = get_hr_trends_df(province_name, region_name)

    #=== Plot the actual Trends data
    trends_fig = go.Figure()    
    trends_fig.add_trace(
        go.Scatter(
            x=df_trends['date'],
            y=df_trends['trend_val'],
            name='Actual Trends',
        )
    )
    
    #=== Create and plot a constant extrapolation of trends
    start_date = df_trends.date.max()
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date = daterange[1]
    rng = pd.date_range(start_date, end_date)
    df_trends_constant = pd.DataFrame({'date': rng,
                                      'trend_val': facemask_slider * np.ones(len(rng))})
    trends_fig.add_trace(
        go.Scatter(
            x=df_trends_constant['date'],
            y=df_trends_constant['trend_val'],
            name='Predicted Trends',
        )
    )
    
    trends_fig.update_layout(xaxis_title='Date',
                             yaxis_title='Google Searches for Face Masks (arb units)',
                             paper_bgcolor = graph_background_color,
                             plot_bgcolor = graph_plot_color,                           
                             margin = graph_margins,
                             xaxis_range = daterange,
                             showlegend=False,                           
                             )
    
    print("END   --- update_trends_chart \t\t", nowtime())

    return trends_fig #, facemask_fig

#=====================================================
#===========  Helper Functions: General  =============
#=====================================================

def get_last_trends_mob_vaxrate_for_region(province_name, region_name):
    """Get values for sliders based on health region"""
    # get the 7-day rolling average of mobility for the region
    df_mob = get_hr_mob_df(province_name, region_name)
    # and the last value of that rolling average
    last_mob = -1*get_last_val('mob', df_mob)
    
    # load fraction_vaccinated data and get last value
    df_vac = get_hr_vac_data(province_name, region_name)
    last_vax_fraction = get_last_val('vac', df_vac)

    # calculate the vaccination rate over last two weeks
    start_date_str = df_vac.date.max()
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
    two_weeks_ago = start_date - datetime.timedelta(days=14)
    two_weeks_ago_str = two_weeks_ago.strftime("%Y-%m-%d")
    two_weeks_vac = \
        df_vac[df_vac.date.between(two_weeks_ago_str, start_date_str)]\
        ['fraction_vaccinated'].to_list()
    last_vax_rate_per_week = (two_weeks_vac[-1] - two_weeks_vac[0])/2.0

    # Vaccination percentage depends on whether the numbers are
    # for the province or the health region
    last_vax_rate_percent = last_vax_rate_per_week * 100 

    #=== Get 7-day rolling average of Google trends
    df_trends = get_hr_trends_df(province_name, region_name)
    # and the last value of that average
    last_trends = get_last_val('trends', df_trends)

    return last_trends, last_mob, last_vax_rate_percent    
    
def get_last_val(type_str, datavar):
    """Get last value in various dataframes"""
    if (type_str == 'mob'):
        # get last rolling average from dataframe of mobility
        return datavar['workplaces_percent_change_from_baseline'].to_list()[-1]
    elif (type_str == 'vac'):
        return datavar['fraction_vaccinated'].to_list()[-1]
    elif (type_str == 'trends'):
        return datavar['trend_val'].to_list()[-1]

def get_val_on_date(type_str, datavar, day):
    """Get value on a date from various dataframes"""    
    day_str = day.strftime("%Y-%m-%d")
    if (type_str == 'mob'):
        df = datavar[datavar.date.between(day_str,day_str)]\
            ['workplaces_percent_change_from_baseline']
        if df.empty:
            # must be past "now", so give slider value
            #print(day_str, "no mob data")
            return no_data_val
        else:
            return df.to_list()[0]
    elif (type_str == 'vac'):
        df = datavar[datavar.date.between(day_str,day_str)]\
            ['fraction_vaccinated']
        if df.empty:
            # must be past "now", so give slider value
            #print(day_str, "no vac data")            
            return no_data_val
        else:
            val = df.to_list()[0]
            if math.isnan(val):
                return 0.0
            else:
                return val
    elif (type_str == 'trends'):
        df = datavar[datavar.date.between(day_str,day_str)]\
            ['trend_val']
        if df.empty:
            # must be past "now", so give slider value
            #print(day_str, "no trends data")                        
            return no_data_val
        else:
            return df.to_list()[0]

def get_linear_extrap_vax(last_vax_fraction, vax_fraction_per_week,
                            max_vax_fraction, days_since_last, df=None):
    """Extrapolate the vaccine data using the rate over past two weeks"""
    if df is None:
        linear_extrap = \
            last_vax_fraction \
            + vax_fraction_per_week * days_since_last / 7.0
        return min(linear_extrap, max_vax_fraction)
    else:
        # if working with dataframe, the variable
        # days_since_last is a string column header
        newdf = df.copy()
        for index, row in newdf.iterrows():
            days = row[days_since_last]
            newdf.at[index, 'linear_extrap'] = \
                min(last_vax_fraction 
                    + vax_fraction_per_week * days / 7.0,
                    max_vax_fraction)
        return newdf

def possibly_replace_w_slider(type_str, val, slider_val):
    """When forecasting, if no data found (future), 
    replace with slider value"""
    if ( (type_str == 'mob') | (type_str == 'trends') ):
        if (val == no_data_val):
            return slider_val
        else:
            return val
    elif (type_str == 'vac'):
        if (val == no_data_val):
            vax_fraction_per_week = slider_val[0]
            last_vax_fraction = slider_val[1]
            max_vax_fraction = slider_val[2]            
            days_since_last = slider_val[3]
            linear_extrap = \
                get_linear_extrap_vax(last_vax_fraction,
                                      vax_fraction_per_week,
                                      max_vax_fraction,
                                      days_since_last)
            return linear_extrap
        else:
            return val
    
def nowtime():
    """return current timestamp"""
    return datetime.datetime.now().time()

def update_province_name(province_name):
    """Update some province names to abbreviated form"""
    if (province_name == "Newfoundland and Labrador"):
        province_name = "NL"
    elif (province_name == "British Columbia"):
        province_name = "BC"
    elif (province_name == "Prince Edward Island"):
        province_name == "PEI"
    elif (province_name == "Northwest Territories"):
        province_name == "NWT"
    return province_name

def get_daterange(forecast_startdate, forecast_length_months):
    """ Return the date range for plotting all graphs.
        Use a fixed start date (first date of mortality)
        and just adjust the maxdate depending on forecast 
    """
    fc_start = datetime.datetime.strptime(forecast_startdate, "%Y-%m-%d")
    fc_length = datetime.timedelta(days=forecast_length_months*days_in_month)
    today = datetime.datetime.now()
    maxdate = max(today, fc_start + fc_length)
    if (maxdate > last_possible_date):
        maxdate = last_possible_date
    return [first_mortality_date_str, maxdate.strftime("%Y-%m-%d")]

#=========================================================
#===========  Helper Functions: Static Data  =============
#=========================================================

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

def get_annual_death(province_name, region_name):
    ann_death_1997 = get_region_info(province_name, region_name).anndeath.item()
    return population_factor_1997_to_today * ann_death_1997

def get_frac_pop_over_80(province_name, region_name):
    frac_over_80 = get_region_info(province_name, region_name).pop80.item()
    return frac_over_80 / get_total_pop(province_name, region_name)

def get_pwpd(province_name, region_name):
    return get_region_info(province_name, region_name).pwpd.item()

def get_pop_sparsity(province_name, region_name):	
    return get_region_info(province_name, region_name).pop_sparsity.item()

def get_provinceid(province_name, region_name):
    # Gets the province abbreviation for the health region
    weat_info_province = static_data[static_data.province_name == province_name]
    return weat_info_province.prov_id[weat_info_province.health_region == region_name].item()

def get_hruid(province_name, region_name):
    # Gets the hr_uid for the health region
    weat_info_province = static_data[static_data.province_name == province_name]
    return weat_info_province.hr_uid[weat_info_province.health_region == region_name].item()

#=========================================================
#===========  Helper Functions: Simulations  =============
#=========================================================
def get_logsmoothed_initial_mortality(the_date, df):
    dfnew = df[['date', 'deaths']].copy()
    # get the 7-day rolling average data
    dfnew['deaths'] = dfnew['deaths'].rolling(window=7).mean()
    # Create a smooth version of that data by logging and
    # interpolating over the places where deaths=0.
    #
    # Note, however that this will not interpolate to the end
    # of the dateframe if they contain zeros
    dfnew['logdeaths'] = 0.0
    for index, row in dfnew.iterrows():
        if row.deaths == 0.0:
            # no data from zero-mortality days 
            dfnew.at[index, 'logdeaths'] = np.nan
        else:
            # otherwise get log(deaths)
            dfnew.at[index, 'logdeaths'] = np.log(row.deaths)
    # doing a centered rolling average here, so might want to move the
    # forecast data backwards by a week so as not to depend on future data
    dfnew['logdeaths'] = \
        dfnew['logdeaths'].rolling(window=15, center=True).mean()
        #dfnew['logdeaths'].rolling(window=15, center=True, min_periods=8).mean()    
    try:
        dfnew['logdeaths'] = \
            dfnew['logdeaths'].interpolate(method='polynomial', order=2)
        # replace deaths with exp(interpolated(smoothed(log(deaths))))
        dfnew['deaths'] = np.exp(dfnew['logdeaths'])
        the_date_ind = \
            pd.to_numeric(
                dfnew.index[dfnew.date.between(the_date, the_date)]
            )[0]
        the_val = dfnew.at[the_date_ind, 'deaths']
        the_new_date_ind = dfnew['deaths'].last_valid_index()
    except:
        the_val = np.nan
        the_new_date_ind = None
        dfnew = None
    if math.isnan(the_val):
        # Because of the centered rolling average, the requested date
        # *will* return nan here... but then if the dataset is full,
        # it will return a date 7 days earlier
        if the_new_date_ind is None:
            # if no valid data, then forecast cannot be done
            print("      --- update_mortality_chart \t\tfell back to original IC method.")
            #return [-1, None, dfnew]
            return [-1, None, None]
        else:
            the_new_date_str = \
                dfnew.date.dt.strftime("%Y-%m-%d").loc[the_new_date_ind]
            return [dfnew.at[the_new_date_ind, 'deaths'],
                    the_new_date_str,
                    dfnew]
    else:
        #=== This shouldn't ever happen, but I guess if it does
        print("      --- update_mortality_chart \t\tfell back to original IC method.")
        return [-1, None, None]

def get_forecasted_mortality(province_name, region_name,
                             forecast_startdate_str, months_to_forecast, 
                             df_mortality, df_mobility, df_vac, df_weather, df_trends,
                             mob_slider_negative, vac_slider_fraction,
                             last_vax_fraction, max_vax_fraction,
                             facemask_slider):
    #=== Calculate some static values
    total_pop = get_total_pop(province_name, region_name)
    annual_death = get_annual_death(province_name, region_name)
    # population over which we have vaccination statistics
    vax_pop = get_total_pop_for_vax_percent(province_name, region_name)
    # Annual death is the static (1997-adjusted) value, not updated by COVID deaths
    xLogAnnual = math.log(annual_death, 10)
    # Average number of people/household
    xHouse = get_avg_house(province_name, region_name)
    # Population-weighted population density (PWPD) times fraction of pop over 80
    pwpd = get_pwpd(province_name, region_name)    
    xLogPWPD = math.log(pwpd * get_frac_pop_over_80(province_name, region_name), 10)
    # Population sparsity value
    land_area = get_land_area(province_name, region_name)
    xBeta = math.log( (total_pop/land_area) / pwpd ) / math.log(0.25**2/land_area)
    
    #=== Get mortality df up to (and including) the forecast_startdate_str
    #    using a copy of the already loaded region-specific mortality df.
    #
    #    The copy will be updated with the simulation data and eventually returned
    df_mort_new = \
        df_mortality[df_mortality.date_death_report\
                     .between(first_mortality_date, forecast_startdate_str)]\
                     [['date_death_report', 'deaths']].copy()
    # simplify date column name
    df_mort_cols = ['date', 'deaths']
    df_mort_new.columns = df_mort_cols
    
    #=== Calculate initial value of deaths for the simulation and get
    #    new mortality dataframe ending at forecast start
    #
    thetype = simulation_initial_value_type
    df_mort_logsmooth = None
    while True:
        if (thetype == 'use_7day_rolling_avg'):
            initial_mortality_on_forecast_startdate = \
                get_random_mortality_rolling_avg_at_end(df_mort_new, randomize=False)
            break
        elif (thetype == 'log_smoothed'):
            #== get the logsmoothed value of the mortality up to the
            #   forecast date, where:
            #      logsmoothed(deaths) = exp(interpolated(smoothed(log(deaths))))
            val, new_date_str, df_mort_logsmooth = \
                get_logsmoothed_initial_mortality(forecast_startdate_str,
                                                  df_mort_new)
            if (val > 0):
                #=== keep if it worked and reset the start date 
                new_forecast_date_str = new_date_str
                initial_mortality_on_forecast_startdate = val
                forecast_startdate_str = new_forecast_date_str
                df_mort_new = \
                    df_mortality[df_mortality.date_death_report\
                                 .between(first_mortality_date, forecast_startdate_str)]\
                                 [['date_death_report', 'deaths']].copy()
                # simplify date column name
                df_mort_cols = ['date', 'deaths']
                df_mort_new.columns = df_mort_cols
                break
            else:
                #=== otherwise, fall back to the other method
                #    ... will likely give azero-valued simulation
                thetype = 'use_7day_rolling_avg'
    #=== Calculate total actual COVID deaths through this day
    total_deaths = df_mort_new['deaths'].sum()

    #=== Extend the mortality dataframe's dates to last day of forecast
    firstdate = df_mort_new.date.min()
    forecast_startdate = datetime.datetime.strptime(forecast_startdate_str, '%Y-%m-%d')
    forecast_enddate = forecast_startdate \
        + datetime.timedelta(days=(months_to_forecast * days_in_month))
    daterng = pd.date_range(firstdate, forecast_enddate)
    df_mort_new = df_mort_new.set_index('date').reindex(daterng).reset_index()
    df_mort_new.columns = df_mort_cols
    #=== Set the mortality on the start date to be the 7day avg value
    df_mort_new.at[df_mort_new.date == forecast_startdate, 'deaths'] = \
        initial_mortality_on_forecast_startdate
    # get index of the start date
    start_index = \
        df_mort_new.index[df_mort_new.date == forecast_startdate].to_list()[0]
    #=== Set mortality values for future dates to zero
    df_mort_new.at[df_mort_new.index > start_index, 'deaths'] = 0.0
    #=== Make a new column for lambda (exp growth rate)
    df_mort_new['lambda'] = 0.0

    #=== Create some time offset values
    two_weeks = datetime.timedelta(days=14)
    four_weeks = datetime.timedelta(days=28)
    fortytwo_days = datetime.timedelta(days=42)
    two_months = datetime.timedelta(days=60)    
    
    #=== Loop over dates of the forecast period
    for index, row in df_mort_new.iterrows():
        #=== ignore dates before the forecast period
        if (index > start_index):
            #=== Get current date in the forecast
            date_in_forecast = row.date
            date_in_forecast_str = date_in_forecast.strftime('%Y-%m-%d')
            # used to calculated predicted vaccination in the future
            days_since_today =  (date_in_forecast - datetime.datetime.now()).days
            
            #=== xHerd is Total Covid Death/Annual Death
            total_deaths = \
                df_mort_new[df_mort_new.date < date_in_forecast]['deaths'].sum()
            xHerd = total_deaths / annual_death
            #=== xHerd2 is the total deaths prior to two-months-ago
            total_deaths_prior_to_two_months_ago = \
                df_mort_new[df_mort_new.date
                            < (date_in_forecast - two_months)]['deaths'].sum()                
            xHerd2 = total_deaths_prior_to_two_months_ago / annual_death
            
            #=== Google facemask trends (4 weeks ago, or slider value if not found)
            xTrends1 = get_val_on_date('trends', df_trends,
                                       date_in_forecast - fortytwo_days)
            xTrends1 = possibly_replace_w_slider('trends', xTrends1, facemask_slider)
            #=== Mobility (two and four weeks ago, or slider value if not found)
            xMob1 = get_val_on_date('mob', df_mobility,
                                    date_in_forecast - two_weeks)
            xMob1 = possibly_replace_w_slider('mob', xMob1, mob_slider_negative)
            xMob2 = get_val_on_date('mob', df_mobility,
                                    date_in_forecast - four_weeks)
            xMob2 = possibly_replace_w_slider('mob', xMob2, mob_slider_negative)            
            
            #=== Weather value is 14d average centered three weeks prior (21d)
            xTemp = get_weather_avg_for_day(df_weather, date_in_forecast, 14, 21)

            #=== Get fraction_vaccinated value
            #       (two and four weeks ago, or slider value if in future)
            vaxP1 = get_val_on_date('vac', df_vac, date_in_forecast - two_weeks)
            vaxP1 = \
                possibly_replace_w_slider('vac', vaxP1,
                                          [vac_slider_fraction,
                                           last_vax_fraction, max_vax_fraction,
                                           days_since_today])
            vaxP2 = get_val_on_date('vac', df_vac, date_in_forecast - four_weeks)
            vaxP2 = \
                possibly_replace_w_slider('vac', vaxP2,
                                          [vac_slider_fraction,
                                           last_vax_fraction, max_vax_fraction,
                                           days_since_today])            

            #=== Past two weeks of death are those since two weeks ago
            #        (future values are zero)
            deaths_past_two_weeks = \
                df_mort_new[df_mort_new.date
                            > (date_in_forecast - two_weeks)]['deaths'].sum()

            #===BPH-FIXME Been having problems with vax data
            #             not sure if this is now fixed or if we'll still get
            #             bad values
            #if ( (1 - 0.9*vaxP2) <= 0):
            #    print(f"*** Error ***  vaxP2 = {vaxP2:f} --> log(1-0.9*vaxP2) < 0")
            if (vaxP1 > 1):
                vaxP1 = 1.0
            if (vaxP2 > 1):
                vaxP2 = 1.0
                
            
            #=== Calculate the dynamic contributions to lambda
            dynamic_lambda = math.exp(
                0.5 * (-7.50188 - 34.5879 * (xHerd - xHerd2) - 1.51981 * xHerd2 +
                       0.011227 * xMob1 + 0.0296737 * xMob2 +
                       0.00476657 * (-26.5794 + xTemp)**2 +
                       0.000143682 * (-26.5794 + xTemp)**3 - 0.0244824 * xTrends1 +
                       xLogPWPD * math.log(10.0)
                       + math.log(1 - maximum_vaccine_effectiveness * vaxP2) + 
                       (2.0 * math.log(8.0 * 10.0**(-xLogPWPD) * (2.0 - 0.5 * xBeta)))
                       / (4.0 - xBeta))
            )
            lambda_val = -0.0398673 + dynamic_lambda - 0.202278 * (vaxP1 - vaxP2) \
                - 0.00654545 * (-3.65 + xLogAnnual) + 0.0201251 * (-2.7 + xHouse)

            #=== Apply a Gaussian random error to lambda value
            sigma = math.sqrt(0.093 / (14.0 + deaths_past_two_weeks))
            lambda_err = random.gauss(0.0, sigma)
            lambda_val += lambda_err
            
            #=== Save lambda value
            df_mort_new.at[index, 'lambda'] = lambda_val
            
            #=== Calculate the new death value
            new_deaths = math.exp(lambda_val) * df_mort_new.at[index-1, 'deaths']
            df_mort_new.at[index, 'deaths'] = new_deaths
            
            # print data to user
            #print(row.date, new_deaths)
    # return dataframe with forecast, and (if doing "logsmoothed")
    # the updated forecast startdate, along with the logsmoothed df
    return [df_mort_new, forecast_startdate_str, df_mort_logsmooth]


#=========================================================
#===========   Helper Functions: Mortality   =============
#=========================================================

def get_hr_mortality_df(province_name, region_name, getall=True,
                        startdate=None, enddate=None):
    dfp = df_mort_all[df_mort_all.province == province_name]
    dfr = dfp[dfp.health_region == region_name].copy()
    if (region_name == "Toronto"):
        #=== Get rid of this Toronto data dump:
        #
        #             date       deaths
        #          29Sep2020     1
        #          30Sep2020     2
        #           1Oct2020     1
        #           2Oct2020     80
        #           3Oct2020     37
        #           4Oct2020     3
        #           5Oct2020     3
        #           6Oct2020     2
        #
        #    According to these articles:
        #
        #     https://www.cbc.ca/news/canada/toronto/
        #                  covid-19-coronavirus-ontario-october-2-1.5747709
        #     https://www.cbc.ca/news/canada/toronto/
        #                  ontario-covid-19-cases-october-3-update-1.5749382
        #     https://www.cbc.ca/news/canada/toronto/
        #                  ontario-covid-19-cases-october-4-update-1.5749841
        #
        #    The spike was due to a "data review and data cleaning
        #    initiative" by Toronto Public Health, and the old cases were
        #    from the "spring or summer" of 2020.  The breakdown was:
        #
        #        oct 1: 3 new
        #        oct 2: 2 new 74 old
        #        oct 3: 4 new 37 old
        #        oct 4: 4 new 3 old
        #
        # reset october 2nd and 3rd values to correct
        therowindex = dfr.index[dfr.date_death_report.between("2020-10-02", "2020-10-02")]
        dfr.at[therowindex, 'deaths'] = 2
        therowindex = dfr.index[dfr.date_death_report.between("2020-10-03", "2020-10-03")]
        dfr.at[therowindex, 'deaths'] = 4
        # distribute remaining 111 cases over prior days, proportional
        # to their existing mortality counts
        old_deaths = 111.0
        df_prior = dfr[dfr.date_death_report.between(first_mortality_date, "2020-10-01")]
        total_deaths_prior = df_prior.deaths.sum()
        for index, row in df_prior.iterrows():
            dfr.at[index, 'deaths'] = \
                dfr.at[index, 'deaths'] \
                + old_deaths * (dfr.at[index, 'deaths'] / total_deaths_prior)
    if getall:
        return dfr
    else:
        if ( (startdate is None) | (enddate is None) ):
            print("***Error: must set start and end dates for getall=False (get_hr_mortality_df)")
            exit(0)
        return dfr[dfr.date_death_report.between(startdate, enddate)]

def get_hr_cases_df(province_name, region_name, getall=True, startdate=None, enddate=None):
    dfp = df_cases_all[df_cases_all.province == province_name]
    dfr = dfp[dfp.health_region == region_name]
    if getall:
        return dfr
    else:
        if ( (startdate is None) | (enddate is None) ):
            print("***Error: must set start and end dates for getall=False (get_hr_cases_df)")
            exit(0)
        return dfr[dfr.date_report.between(startdate, enddate)]

def get_random_mortality_rolling_avg_at_end(df, randomize=True):
    last_rolling_avg = df.deaths.rolling(window=7).mean().to_list()[-1]
    if randomize:
        return np.random.poisson(7.0 * last_rolling_avg) / 7.0
    else:
        return last_rolling_avg        

def get_dates_list(province_name, region_name, start_date, end_date):
    """Used for cumulative_deaths and R(t)"""
    df = get_hr_mortality_df(province_name, region_name, getall=False,
                             startdate=start_date, enddate=end_date)
    return df.date_death_report.dt.strftime("%Y-%m-%d").to_list()
            
def get_cumulative_deaths(province_name, region_name, start_date, end_date):
    #===BPH-FIXME:  don't think we need mm/dd/YYYY here?
    start_date_str = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%m-%d-%Y')
    end_date_str = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%m-%d-%Y')

    filtered_df2 = df_mort_all[df_mort_all.date_death_report.between(
        start_date_str, end_date_str
    )]
    df_province = filtered_df2[filtered_df2.province == province_name]
    
    deaths = df_province.cumulative_deaths[df_province.health_region == region_name] #.rolling(window=7).mean()
    return deaths

#=========================================================
#===========   Helper Functions: Cases       =============
#=========================================================


#=========================================================
#===========   Helper Functions: Mobility    =============
#=========================================================

#===BPH-FIXME: I've deleted this and I'm not sure where/when it is necesary...
#              I did implement a pandas interpolate over nan values in the mob
#              data file, but I didn't check if all dates are there. Should do that.
def interpolate_mob_dates(province_name, region_name, start_date, end_date, months_to_forecast):

    base = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    add_dates = [base + datetime.timedelta(days=x) for x in range(months_to_forecast * days_in_month)]

    for i in range(len(add_dates)):
        add_dates[i] = datetime.datetime.strptime(str(add_dates[i]), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
    
    return add_dates

def get_hr_mob_df(province_name, region_name, getall=True, startdate=None, enddate=None):
    weat_info_province = static_data[static_data.province_name == province_name]
    sub_region = weat_info_province.sub_region_2[weat_info_province.health_region == region_name].item()
    df_mob = df_mob_all[df_mob_all.sub_region_2 == sub_region].copy()
    df_mob = df_mob[['date', 'workplaces_percent_change_from_baseline']]
    #=== Get the 7-day rolling average of mobility always
    df_mob['workplaces_percent_change_from_baseline'] = \
        df_mob['workplaces_percent_change_from_baseline'].rolling(window=7).mean()
    #=== Interpolate the mobility data to fill in blanks
    df_mob['workplaces_percent_change_from_baseline'] = \
        df_mob['workplaces_percent_change_from_baseline'].interpolate(method='polynomial', order=3)
    if getall:
        return df_mob
    else:
        if ( (startdate is None) | (enddate is None) ):
            print("***Error: must set start and end dates for getall=False (get_hr_mob_df)")
            exit(0)
        return df_mob[df_mob.date.between(startdate, enddate)]

#=========================================================
#===========   Helper Functions: Weather     =============
#=========================================================

def get_weather_dataframe(province_name, region_name):
    # Get weather dataframe
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
    prov_id = get_provinceid(province_name, region_name)
    hr_uid = get_hruid(province_name, region_name)
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

#=========================================================
#===========  Helper Functions: Vaccination  =============
#=========================================================

def get_total_pop_for_vax_percent(province_name, region_name):
    regional_population = get_total_pop(province_name, region_name)
    provincial_population = get_prov_pop(province_name, region_name)
    vax_data_type = check_vax_data_type(province_name)
    if (vax_data_type == 'provincial'):
        return provincial_population
    else:
        return regional_population

def check_vax_data_type(province_name):
    if ( (province_name == 'Alberta') or (province_name == 'New Brunswick')
         or (province_name == 'NL') or (province_name == 'Nova Scotia') ):
        return 'provincial'
    else:
        return 'regional'

def get_uid(province_name, region_name):
    uid = get_region_info(province_name, region_name).hr_uid.item()
    return uid

def get_hr_vac_data(province_name, region_name):
    #=== Check whether regional data available (or only provincial)
    vax_data_type = check_vax_data_type(province_name)
    if (vax_data_type == "provincial"):
        api = vac_base_url_prov + str(get_provinceid(province_name, region_name))
    else:
        api = vac_base_url + str(int(get_uid(province_name, region_name)))
    #=== Download the data into a json files
    with request.urlopen(str(api)) as response:
        source = response.read()
        api_data = json.loads(source)['data']
    #=== Convert into pandas dataframe
    df = pd.json_normalize(api_data, max_level=1)
    
    #=== Data from Govt of Canada show that 11.5% of doses distributed
    #    to each province as of 12May2021 are AZ (and no J&J):
    #
    #         https://www.canada.ca/en/public-health/services/diseases
    #             /2019-novel-coronavirus-infection/prevention-risks
    #             /covid-19-vaccine-treatment/vaccine-rollout.html
    #
    #    Thus 11.5% of vaccinations can be assumed full and the
    #    rest are half.
    #
    #        set frac_vax_one_dose = 0.115
    #
    #=== Define an estimate of total vaccinated per population
    pop = get_total_pop_for_vax_percent(province_name, region_name)
    df['fraction_vaccinated'] = \
        ( (1.0 - frac_vax_one_dose) * df['total_vaccinations'] / 2.0
          + frac_vax_one_dose * df['total_vaccinations'] ) / pop
    #=== Return only relevant information
    return df[['date', 'fraction_vaccinated']]

#=========================================================
#===========  Helper Functions: Google-Trends  ===========
#=========================================================

def get_geocode(province_name, region_name):
    geo_code = get_region_info(province_name, region_name).geo_code.item()
    return str(geo_code)

def get_hr_trends_df(province_name, region_name, getall=True,
                     startdate=None, enddate=None):
    #===BPH get both date and the trends data
    geocode = get_geocode(province_name, region_name)
    df_trends = df_trends_all[['date', geocode]].copy()
    # rename columns
    trends_cols = ['date', 'trend_val']
    df_trends.columns = trends_cols
    if (province_name == "Quebec"):
        df_trends.trend_val = df_trends.trend_val * trends_mult_factor_for_QC
    #===BPH apply a smooth increase around 15Apr2020, when CDC first
    #       recommended mask use
    df_trends['days_since_15apr2020'] = \
        ( df_trends['date'] - datetime.datetime.strptime("2020-04-15", "%Y-%m-%d") ).dt.days
    df_trends['trend_val'] = \
        0.5 * df_trends['trend_val']\
        * ( 1.0 + np.tanh(df_trends['days_since_15apr2020']/14.0) )
    # remove the days since 15Apr
    df_trends = df_trends[trends_cols]
    #=== Get the 7-day rolling average of trends, always
    df_trends['trend_val'] = df_trends['trend_val'].rolling(window=7).mean()
    if getall:
        return df_trends
    else:
        if ( (startdate is None) | (enddate is None) ):
            print("***Error: must set start and end dates for getall=False (get_hr_mortality_df)")
            exit(0)
        return df_trends[df_trends.date.between(startdate, enddate)]

#=========================================================
#===========  Helper Functions: R(t) graph     ===========
#=========================================================

def calculate_Rt_from_mortality(df_mort):
    #=== Calculate R(t) from mortality data:
    #
    #    * for exp growth with fixed serial interval, tau:
    #
    #           n(tau) = n0 * R
    #           n(2*tau) = (n0 * R) * R
    #           n(N*tau) = n0 R^N
    #           n(t) = n0 R^(t/tau)
    #                = n0 exp[t/tau ln(R)]
    #                = n0 exp[lambda*t]     w/ lambda = ln(R)/tau
    #
    #              ---> R = exp(tau*lambda)
    #
    #    * Get D_14 = 14-day rolling average of mortality
    #
    #    * Assuming
    #
    #          D_14(t) = const * exp[ lambda * t ]
    #
    #      we have (natural log)
    #
    #          lambda(t) = d[log(D_14)]/dt
    #
    #      which can be calculated using numpy.gradient
    #
    #    * Calculate
    #
    #          R(t) = exp[ tau * lambda(t) ] 
    #   
    #    * Take 14-day rolling average of the resulting R(t)
    #
    df_mort_Rt = df_mort.copy()
    df_mort_Rt['D14'] = \
        df_mort_Rt['deaths'].rolling(window=14).mean() + Rt_make_D14_nonzero_offset
    df_mort_Rt['log_D14'] = np.log(df_mort_Rt['D14'])
    if Rt_smooth_lambda14_first:
        df_mort_Rt['lambda_14'] = np.gradient(df_mort_Rt['log_D14'])
        df_mort_Rt['lambda_14'] = df_mort_Rt['lambda_14'].rolling(window=14).mean()
        df_mort_Rt['Rt'] = np.exp( Rt_serial_interval
                                   * df_mort_Rt['lambda_14'] )
    else:
        df_mort_Rt['lambda_14'] = np.gradient(df_mort_Rt['log_D14'])
        df_mort_Rt['Rt'] = np.exp( Rt_serial_interval
                                   * df_mort_Rt['lambda_14'] )
        df_mort_Rt['Rt'] = df_mort_Rt['Rt'].rolling(window=14).mean()

    return df_mort_Rt

# ======================= END OF PROGRAM =======================

if __name__ == "__main__":
    app.run_server(debug=True)
