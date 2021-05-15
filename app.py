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
number_of_simulations = 2

#== Turn the navbar on/off
navbar_on = False

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
initial_daterange_min = first_mortality_date
initial_daterange_max = last_mortality_date
#=== Set initial slider values to negative, so that initial
#    runs of graphs will get updated values for the region
initial_facemask_slider = -1
initial_mobility_slider = -1
initial_vaccine_slider = -1

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
                                                    children="Date Range",
                                                    className="dropdown-title",
                                                    id = "placeholder"
                                                    ),
                                                dcc.DatePickerRange(
                                                    id="date-range",
                                                    min_date_allowed=first_mortality_date.date(),
                                                    max_date_allowed=last_possible_date.date(),
                                                    initial_visible_month=last_mortality_date.date(),
                                                    start_date = initial_daterange_min.date(),
                                                    end_date = initial_daterange_max.date(),
                                                    #min_date_allowed=df_mort_all.date_death_report.min().date(),
                                                    #max_date_allowed=df_mort_all.date_death_report.max().date(),
                                                    #initial_visible_month=df_mort_all.date_death_report.max().date(),
                                                    #start_date=df_mort_all.date_death_report.min().date(), # "2020-03-13"
                                                    #end_date=df_mort_all.date_death_report.max().date(), #"2021-03-31"
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
                                                    children="Face Mask Google Trends",
                                                    className="dropdown-title"
                                                    ),
                                                dcc.Slider(
                                                    id='facemask-slider',
                                                    min=0,
                                                    max=100,
                                                    step=1,
                                                    value=initial_facemask_slider,
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
                                                    value=initial_mobility_slider,
                                                    marks={
                                                        0: '0% (normal)',
                                                        25: '25%',
                                                        50: '50%',
                                                        75: '75%',
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
                                                    max=12,
                                                    step=0.5,
                                                    value=forecast_initial_length, 
                                                    marks={ 0: '0 mo', 2: '2 mo', 4: '4 mo',
                                                        6: '6 mo', 8: '8 mo', 10: '10 mo', 12: '1 yr'
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
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks'),
        ddp.Input('subregion-dropdown', 'value')
    ],
    [
        ddp.State('region-dropdown', 'value'),
    ]
)
def update_static_cards(n_clicks1, n_clicks2, region_name, province_name):

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
        ddp.Input('rerun-btn1', 'n_clicks'),        
        ddp.Input('rerun-btn2', 'n_clicks'),
        ddp.Input('subregion-dropdown', 'value'),
    ],
    [
        ddp.State('region-dropdown', 'value'),
    ]
)
def update_dynamic_cards(n_clicks1, n_clicks2, region_name, province_name):

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
        ddp.Input('rerun-btn1', 'n_clicks'),
        ddp.Input('rerun-btn2', 'n_clicks'),
        ddp.Input('subregion-dropdown', 'value')        
    ],
    [
        ddp.State('region-dropdown', 'value'),
    ]
)
def update_headers(n_clicks1, n_clicks2, region_name, province_name):

    print("START --- update_static_cards \t\t", nowtime())
    
    province_name = update_province_name(province_name)

    # Graph Titles
    deaths_label = 'Daily Deaths in ' + region_name + ', ' + province_name 
    cases_label = 'Daily Reported Cases in ' + region_name + ', ' + province_name
    mob_label = 'Workplace Social Mobility in ' + region_name + ', ' + province_name
    temp_label = 'Daily Reported Temperature in ' + region_name + ', ' + province_name
    vac_label = 'Fraction of the Population Vaccinated in ' + region_name + ', ' + province_name
    trends_label = 'Google Searches for Face Masks in ' + region_name + ', ' + province_name
    rtcurve_label = 'Effective Reproduction Number R(t) Curves in ' + region_name + ', ' \
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
    ],
)
def update_mortality_chart(n_clicks1, n_clicks2, region_name, province_name, 
                           day_to_start_forecast, months_to_forecast,
                           facemask_slider, mob_slider,
                           vac_slider, max_vax_percent):    
    
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
    
    print("      --- update_mortality_chart \t", nowtime(), " --- started loading data")
    
    #=== Identify an initial run or an update for the region
    #    and set slider values manually
    if ( (mob_slider < 0) | (facemask_slider < 0) | (vac_slider < 0)
         | (~do_simulations) ):
        facemask_slider, mob_slider, vac_slider = \
            get_last_trends_mob_vaxrate_for_region(province_name, region_name)
    
    print("      --- update_mortality_chart \t", nowtime(), " --- slider data loaded")
        
    #=== Set the daterange (same for all graphs).  This is currently:
    #         [first_mortality_date, forecast_startdate + forecast_length]
    daterange = get_daterange(day_to_start_forecast, months_to_forecast)
    
    #=== Adjust slider values for use in model forecast
    mob_slider_negative = -1*mob_slider
    facemask_slider_adj = facemask_slider * 70.0 / 100.0
    vac_slider_fraction = vac_slider / 100.0
    max_vax_fraction = max_vax_percent / 100
    
    #=== Get the mortality dataframe and make a copy for plotting
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    df_mort = get_hr_mortality_df(province_name, region_name, getall=False,
                                  startdate=daterange[0], enddate=today_str)
    df_mort_plot = df_mort.copy()
    df_mort_plot['deaths'] = df_mort_plot['deaths'].rolling(window=7).mean()    
    
    print("      --- update_mortality_chart \t", nowtime(), " --- mortality loaded")
    
    #===BPH-FIXME: add the R(t) values to the dataframe for similar plotting
    #              their plotting is very slow.
    #
    #=== Get the mortality dataframe and make a copy for plotting
    #df_mort_plot['R(t)'] = 
    
    #=== Get "fraction_vaccinated" dataframe
    df_vac = get_hr_vac_data(province_name, region_name)
    last_vax_fraction = get_last_val('vac', df_vac)
    
    print("      --- update_mortality_chart \t", nowtime(), " --- vaccination loaded")    
    
    #=== Get the 7-day rolling average of the mobility data
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
    
    print("      --- update_mortality_chart \t", nowtime(), " --- finished plotting deaths")
    print("      --- update_mortality_chart \t", nowtime(), " --- started plotting R(t)")
    
    #=== Initialize R(t) figure and plot the R(t) from actual mortality data
    start_date = daterange[0]
    end_date = today_str
    rtcurve_fig = go.Figure()
    rtcurve_fig.add_trace(
        go.Scatter(
            x = get_dates_list(province_name, region_name, start_date, end_date),
            y = past_rt_equation(province_name, region_name, start_date, end_date),
            name='Previous R(t)',
            line=dict(color='black', width=2),
        )
    )
    print("      --- update_mortality_chart \t", nowtime(), " --- finished plotting R(t)")
    print("      --- update_mortality_chart \t", nowtime(), " --- started simulations")    
    if do_simulations:
        #=== Run forecast simulations
        for i in range(number_of_simulations):
            print("      --- update_mortality_chart \t", nowtime(), " --- D(t) CURVE: " + str(i))
            df_forecast = \
                get_forecasted_mortality(province_name, region_name,
                                         day_to_start_forecast, months_to_forecast,
                                         df_mort, df_mobility, df_vac, df_weather, df_trends,
                                         mob_slider_negative,
                                         vac_slider_fraction, last_vax_fraction,
                                         max_vax_fraction,
                                         facemask_slider_adj)
            df_forecast = \
                df_forecast[df_forecast.date.between(day_to_start_forecast, daterange[1])]
            #=== Add simulated forecast of mortality to the mortality figure
            mortality_fig.add_trace(
                go.Scatter(
                    x=df_forecast['date'],
                    y=df_forecast['deaths'],
                    mode = 'lines',
                    name='Prediction ' + str(i+1),
                )
            )
            #=== Add simulated forecast of R(t) to the R(t) figure
            df_forecast['R(t)'] = np.exp( 5.3 * df_forecast['lambda'] )
            rtcurve_fig.add_trace(
                go.Scatter(
                    x = df_forecast['date'].to_list(),
                    y = moving_avg(df_forecast['R(t)'].to_list(), 14),
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
    cumulativedeaths = cumulative_deaths(province_name, region_name, start_date, end_date)
    
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
    ],        
    [
        ddp.State("region-dropdown", "value"),
        ddp.State("forecast-start-date", "date"),
        ddp.State('forecast-slider', 'value'),
        ddp.State('mobility-slider', 'value'),
    ],
)
def update_mob_charts(n_clicks1, n_clicks2, region_name, province_name, 
                      day_to_start_forecast, months_to_forecast, mob_slider):
    print("START --- update_mob_charts \t\t", nowtime())
    #print("      --- update_mob_charts \t\t", nowtime(), " --- xMob=" + str(xMob))

    daterange = get_daterange(day_to_start_forecast, months_to_forecast)
    
    province_name = update_province_name(province_name)

    #=== Check to see if button pressed, or subregion changed
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if ( ('rerun-btn1' in changed_id) | ('rerun-btn2' in changed_id) ):
        button_pressed = True
    else:
        button_pressed = False
    
    #=== Identify an initial run or sub-region change
    #    and set slider values manually
    if ( (mob_slider < 0) | (~button_pressed) ):
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
        )
    )

    #=== Create and plot a constant mobility function
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    start_date = today_str
    end_date = daterange[1]
    rng = pd.date_range(start_date, end_date)
    df_mob_plot_constant = pd.DataFrame({'date': rng,
                                         'mob': mob_slider_neg * np.ones(len(rng))})
    mobility_fig.add_trace(
        go.Scatter(
            x=df_mob_plot_constant['date'],
            y=df_mob_plot_constant['mob'],
            name='Predicted Mobility',
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
    
    #=== Check to see if button pressed, or subregion changed    
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if ( ('rerun-btn1' in changed_id) | ('rerun-btn2' in changed_id) ):
        button_pressed = True
    else:
        button_pressed = False

    #=== Identify an initial run or a region update
    #    and set slider values manually
    if ( (vac_slider < 0) | (~button_pressed) ):
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
            name='Estimated Percent Vaccinated'
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
    ],
    [
        ddp.State("region-dropdown", "value"),
        ddp.State("date-range", "start_date"),
        ddp.State("date-range", "end_date"),
        ddp.State("forecast-start-date", "date"),
        ddp.State('forecast-slider', 'value'),
        ddp.State('facemask-slider', 'value'),
    ],
)
def update_trends_charts(n_clicks1, n_clicks2, region_name, province_name,
                         start_date, end_date,
                         day_to_start_forecast, months_to_forecast, mask_slider_val):
    print("START --- update_trends_chart \t\t", nowtime())

    daterange = get_daterange(day_to_start_forecast, months_to_forecast)
    
    province_name = update_province_name(province_name)
    
    dates = predicted_dates(province_name, region_name, end_date, months_to_forecast)
    trends_vals = []
    for i in range(len(dates)):
        trends_vals.append(mask_slider_val)
        
    df_trends = df_trends_data(province_name, region_name)
    trends_past_dates = df_trends['date']
    trends_past_vals = df_trends[get_geocode(province_name, region_name)]

    trends_fig = px.line(df_trends, x = trends_past_dates, y = trends_past_vals)

    trends_fig.add_trace(go.Scatter(
            x=dates,
            y=trends_vals,
            name='Simulated Facemask Use',
        ))

    trends_fig.update_layout(xaxis_title='Date',
                             yaxis_title='Number of Google Searches for Face Masks',
                             paper_bgcolor = graph_background_color,
                             plot_bgcolor = graph_plot_color,                           
                             margin = graph_margins,
                             xaxis_range = daterange,
                             showlegend=False,                           
                             )
    
    first_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    #===BPH this should have been "2020-04-15" (April 2020 not 2021)
    mid_april = datetime.datetime.strptime("2021-04-15", "%Y-%m-%d").date()
    
    days_since_first_day = first_date - mid_april
    delta = days_since_first_day.days

    facemask_vals = []
    for i in range(len(trends_past_vals)):
        gTrends = trends_past_vals[i]
        fm = gTrends * 0.5 * (1 + (np.tanh(delta) / 14))
        facemask_vals.append(fm)

    facemask_fig = px.line(df_trends, x = trends_past_dates, y = facemask_vals)
    facemask_fig.update_layout(xaxis_title='Date',
                               yaxis_title='7-day Average Facemask',
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
    
# get last value of various things
def get_last_val(type_str, datavar):
    if (type_str == 'mob'):
        # get last rolling average from dataframe of mobility
        return datavar['workplaces_percent_change_from_baseline'].to_list()[-1]
    elif (type_str == 'vac'):
        return datavar['fraction_vaccinated'].to_list()[-1]
    elif (type_str == 'trends'):
        return datavar['trend_val'].to_list()[-1]

def get_val_on_date(type_str, datavar, day):
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
                        
    
# get total of various things over some date range
def get_total(type_str, datavar, date_start, date_end):
    if (type_str == 'vac'):
        # json (list of dictionaries)
        # find last date
        startend_ind = [-1, -1]
        for i in range(len(datavar)):
            if (datavar[i]['date'] == date_start):
                startend_ind[1] = i
            if (datavar[i]['date'] == date_end):
                startend_ind[1] = i
        return datavar[-1]['total_vaccinations']
        
    
# function to return current timestamp
def nowtime():
    return datetime.datetime.now().time()

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

def get_daterange(forecast_startdate, forecast_length_months):
    #===BPH Use a fixed start date (first date of mortality)
    #       and just adjust the maxdate
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

def get_forecasted_mortality(province_name, region_name,
                             forecast_startdate_str, months_to_forecast, 
                             df_mortality, df_mobility, df_vac, df_weather, df_trends,
                             mob_slider_negative, vac_slider_fraction,
                             last_vax_fraction, max_vax_fraction,
                             trends_slider_adj):
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

    #=== Calculate total actual COVID deaths through this day
    total_deaths = df_mort_new['deaths'].sum()

    #=== Calculate the 7dayavg of mortality on the forecast_startdate_str
    #    for matching simulations to the plotted 7-day avg of actual mortality
    #===BPH Removed randomization of death data on first day of prediction
    mort_7dayavg_forecast_start_date = \
        get_random_mortality_rolling_avg_at_end(df_mort_new, randomize=False)

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
        mort_7dayavg_forecast_start_date
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
            
            #=== Google trends (four weeks ago, or slider value if not found)
            xTrends1 = get_val_on_date('trends', df_trends,
                                       date_in_forecast - fortytwo_days)
            xTrends1 = possibly_replace_w_slider('trends', xTrends1, trends_slider_adj)

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
            vaxP2 = get_val_on_date('vac', df_vac,
                                    date_in_forecast - four_weeks) / vax_pop
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
            #             not sure what to do here...
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
            df_mort_new.at[index, 'deaths'] = \
                math.exp(lambda_val) * df_mort_new.at[index-1, 'deaths']
            
    return df_mort_new


#=========================================================
#===========   Helper Functions: Mortality   =============
#=========================================================


#===BPH-FIXME Delete this
def get_total_deaths_old(province_name, region_name, start_date, end_date):
    start_date_str = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%m-%d-%Y')
    end_date_str = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%m-%d-%Y')

    filtered_df2 = df_mort_all[df_mort_all.date_death_report.between(
        start_date_str, end_date_str
    )]
    df_province = filtered_df2[filtered_df2.province == province_name]
    
    deaths = df_province.deaths[df_province.health_region == region_name]

    total_deaths_local = 0 # reset total deaths

    for d in deaths:
        total_deaths_local += d
    
    return total_deaths_local

def get_hr_mortality_df(province_name, region_name, getall=True,
                        startdate=None, enddate=None):
    dfp = df_mort_all[df_mort_all.province == province_name]
    dfr = dfp[dfp.health_region == region_name]
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

def get_dates_list(province_name, region_name, start_date, end_date): # todo: dates are in d-m-y
    df = get_hr_mortality_df(province_name, region_name, getall=False,
                             startdate=start_date, enddate=end_date)
    return df.date_death_report.dt.strftime("%Y-%m-%d").to_list()
    
def get_mortality_rollingavg(province_name, region_name, start_date, end_date): # todo: dates are in d-m-y
    start_date_str = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%m-%d-%Y')
    end_date_str = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%m-%d-%Y')

    df_provmort = df_mort_all[df_mort_all.province == province_name]
    df_provmort_filtered = df_provmort[df_provmort.date_death_report.between(
        start_date_str, end_date_str
    )]
    
    rolling_avgs = df_provmort_filtered.deaths[df_provmort_filtered.health_region == region_name].rolling(window=7).mean()
        
    return rolling_avgs.to_list()

def get_total_deaths_2_months_prior(province_name, region_name, end_date):
    date_up_to = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    first_day = df_mort_all.date_death_report.min().date().strftime('%m-%d-%Y')

    delta_2_months = datetime.timedelta(days=60)
    end_date_2_months_ago = date_up_to - delta_2_months
    end_date_2_months_ago = end_date_2_months_ago.strftime('%m-%d-%Y')
    date_up_to = date_up_to.strftime('%m-%d-%Y')

    df_2_months = df_mort_all[df_mort_all.date_death_report.between(
        first_day, end_date_2_months_ago
    )]
    df_province_2_months = df_2_months[df_2_months.province == province_name]
    deaths_2_months = df_province_2_months.deaths[df_province_2_months.health_region == region_name]

    A = df_mort_all[df_mort_all.date_death_report.between(
        end_date_2_months_ago, date_up_to)]
    B = A[A.province == province_name]
    twomonths_deaths = B.deaths[B.health_region == region_name].to_list()
        
    total_deaths_2_months = 0 # reset total deaths

    for d in deaths_2_months:
        total_deaths_2_months += d

    return [total_deaths_2_months, twomonths_deaths]
    # date_up_to = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    # first_day = df_mort_all.date_death_report.min().date().strftime('%m-%d-%Y')

    # delta_2_months = datetime.timedelta(days=60)
    # end_date_2_months_ago = date_up_to - delta_2_months
    # end_date_2_months_ago = end_date_2_months_ago.strftime('%m-%d-%Y')

    # df_2_months = df_mort_all[df_mort_all.date_death_report.between(
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

    df_2_weeks = df_mort_all[df_mort_all.date_death_report.between(
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

    filtered_df2 = df_mort_all[df_mort_all.date_death_report.between(
        start_date_str, end_date_str
    )]
    df_province = filtered_df2[filtered_df2.province == province_name]
    
    deaths = df_province.cumulative_deaths[df_province.health_region == region_name] #.rolling(window=7).mean()
        
    return deaths
    
#=========================================================
#===========   Helper Functions: Cases       =============
#=========================================================

def get_last_cases(province_name, region_name, start_date, end_date): # todo: d-m-y
    filtered_df = df_cases_all[df_cases_all.date_report.between(
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
    filtered_df = df_cases_all[df_cases_all.date_report.between(
        datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%m-%d-%Y'),
        datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%m-%d-%Y')
    )]
    dfcases_province = filtered_df[filtered_df.province == province_name]
    return dfcases_province.date_report[dfcases_province.health_region == region_name]

def get_total_cases(province_name, region_name, start_date, end_date):
    start_date_str = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_str = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')

    filtered_df2 = df_cases_all[df_cases_all.date_report.between(
        start_date_str, end_date_str
    )]
    df_province = filtered_df2[filtered_df2.province == province_name]
    
    cases = df_province.cases[df_province.health_region == region_name]

    total_cases_local = 0

    for c in cases:
        total_cases_local += c
    
    return total_cases_local

#=========================================================
#===========   Helper Functions: Mobility    =============
#=========================================================

def mobility(province_name, region_name, start_date, end_date):
    filtered_df = df_mob_all[df_mob_all.date.between(
        start_date, end_date
    )]
    weat_info_province = static_data[static_data.province_name == province_name]
    sub_region = weat_info_province.sub_region_2[weat_info_province.health_region == region_name].item()

    return filtered_df.workplaces_percent_change_from_baseline[df_mob_all.sub_region_2 == sub_region].rolling(window=7).mean()

def date_mob(province_name, region_name, start_date, end_date):
    filtered_df = df_mob_all[df_mob_all.date.between(
        start_date, end_date
    )]
    
    weat_info_province = static_data[static_data.province_name == province_name]
    sub_region = weat_info_province.sub_region_2[weat_info_province.health_region == region_name].item()
    
    return filtered_df.date[df_mob_all.sub_region_2 == sub_region]

def interpolate_mob_dates(province_name, region_name, start_date, end_date, months_to_forecast):

    base = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    add_dates = [base + datetime.timedelta(days=x) for x in range(months_to_forecast * days_in_month)]

    for i in range(len(add_dates)):
        add_dates[i] = datetime.datetime.strptime(str(add_dates[i]), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
    
    return add_dates

def get_mob_on_day(df_mobility, day, xMob, days_prior):
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

def get_hr_mob_df(province_name, region_name, getall=True, startdate=None, enddate=None):
    weat_info_province = static_data[static_data.province_name == province_name]
    sub_region = weat_info_province.sub_region_2[weat_info_province.health_region == region_name].item()
    df_mob = df_mob_all[df_mob_all.sub_region_2 == sub_region].copy()
    df_mob = df_mob[['date', 'workplaces_percent_change_from_baseline']]
    #=== Get the 7-day rolling average of mobility always
    df_mob['workplaces_percent_change_from_baseline'] = \
        df_mob['workplaces_percent_change_from_baseline'].rolling(window=7).mean()
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

def get_vaccination_dates(province_name, region_name):
    vac_date = []
    for d in get_vaccination_data(province_name, region_name):
        time = d['date']
        vac_date.append(time)
    return vac_date
    
def get_vaccination_vals(province_name, region_name):
    total_vaccinations = []
    for d in get_vaccination_data(province_name, region_name):
        vaccine = d['total_vaccinations']
        total_vaccinations.append(vaccine)
    return total_vaccinations

def get_vac_on_day(date_in_forecast, vac_val, total_population, df_vac, days_prior, last_vac):
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

def df_vaccinations(province_name, region_name):    
    df_vaccinations = pd.DataFrame(vac_df_data(province_name, region_name), columns = ['date','total_vaccinations'])
    df_vaccinations = df_vaccinations.dropna()
    
    pop = get_total_pop_for_vax_percent(province_name, region_name)
    df_vaccinations['total_vaccinations'] = df_vaccinations.total_vaccinations.div(pop)
    
    return df_vaccinations

def get_frac_vaccinations_1_month_prior(province_name, region_name):
    date_now = datetime.datetime.now() #datetime.datetime.now()
    first_day =df_vac.date.min()
    
    delta_1_month = datetime.timedelta(days=days_in_month)
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

#=========================================================
#===========  Helper Functions: Google-Trends  ===========
#=========================================================

def get_geocode(province_name, region_name):
    geo_code = get_region_info(province_name, region_name).geo_code.item()
    return str(geo_code)

def get_trends_vals(province_name, region_name):
    return df_trends_all[get_geocode(province_name, region_name)]

def get_trends_dates(province_name, region_name):
    return df_trends_all['date']

def df_trends_data(province_name, region_name):
    trends_data = {'date': get_trends_dates(province_name, region_name),
        get_geocode(province_name, region_name): get_trends_vals(province_name, region_name)}
    df_trends = pd.DataFrame(trends_data, columns = ['date', get_geocode(province_name, region_name)])
    return df_trends

def old_get_trends_on_day(province_name, region_name, day, trends):
    days_since_first_day = day.date() - datetime.date(2020, 1, 1)
    delta = days_since_first_day.days - 43 - 11 # todo: remove - 11
    df_dates = df_trends[get_geocode(province_name, region_name)]
    if (delta < len(df_trends.index) and delta >= 0):
        trend_42_days_ago = df_dates[delta]
        if (province_name == "Quebec"):
            trend_42_days_ago = trend_42_days_ago * 2.5
    else:
        trend_42_days_ago = trends
        
    return trend_42_days_ago

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
    #=== Get the 7-day rolling average of trends always
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
    df_2_weeks = df_mort_all[df_mort_all.date_death_report.between(
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

def past_rt_equation(province_name, region_name, start_date, end_date):
    
    D14_values = []
    D14_t5_values = []
    
    #date_D14 = datetime.datetime.today()
    date_D14 = datetime.datetime.strptime(end_date, "%Y-%m-%d")    
    date_D14_t5 = date_D14 - datetime.timedelta(days=4)
    days_prior = 14
    
    #start = datetime.datetime.strptime("2020-03-08", "%Y-%m-%d")
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")    
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
