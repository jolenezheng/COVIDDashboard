# -*- coding: utf-8 -*-
import math
import dash
import dash_table
import random
import requests
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
from dash.dependencies import Output, Input
import plotly.express as px
import plotly.graph_objects as go
import datetime as datetime

from textwrap import dedent
from dateutil.relativedelta import relativedelta

# todo:
# fix dates
# quebec names


df_mort = pd.read_csv('https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_hr/mortality_timeseries_hr.csv', parse_dates=[0], dayfirst=True)
df_mort["date_death_report"] = pd.to_datetime(df_mort["date_death_report"], format="%d-%m-%Y", dayfirst =True)

df_cases = pd.read_csv('https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_hr/cases_timeseries_hr.csv')
df_cases["date_report"] = pd.to_datetime(df_cases["date_report"], format="%d-%m-%Y", dayfirst =True)

weather_base_url = 'https://dd.weather.gc.ca/climate/observations/daily/csv/'
static_data = pd.read_csv(r'data/health_regions_static_data.csv', encoding='Latin-1')

mobility_info = pd.read_csv(r'data/2020_CA_Region_Mobility_Report.csv')
mobility_info["sub_region_2"] = mobility_info["sub_region_2"]

vac_base_url = "https://api.covid19tracker.ca/reports/regions/"
vac_base_url_prov = "https://api.covid19tracker.ca/reports/province/"

current_date = datetime.datetime.strptime("03-31-2021", "%m-%d-%Y") #datetime.datetime.now()
gloabl_date = current_date.strftime('%Y-%m')

prov_id = "ON"
climate_id = 0
target_url = ""
weat_data = None
weat_city = None
date_city = None
# province_name = "Ontario"
# region = "Waterloo"
# start_date = "15-03-2020"
# end_date = datetime.datetime.strftime(datetime.datetime.now(), "%d-%m-%Y")

last_mort = 0
total_deaths = 0


# df_mob = pd.read_csv('https://www.gstatic.com/covid19/mobility/Global_Mobility_Report.csv')


external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]
fnameDict = {    
    "Alberta": ["Calgary","Central","Edmonton","North","South"], 
    "British Columbia":["Fraser","Interior","Island","Northern","Vancouver Coastal"],
    "Manitoba": ["Interlake-Eastern","Northern","Prairie Mountain","Southern Health","Winnipeg"],
    "New Brunswick": ["Zone 1 (Moncton area)","Zone 2 (Saint John area)","Zone 3 (Fredericton area)",
                      "Zone 4 (Edmundston area)","Zone 5 (Campbellton area)","Zone 6 (Bathurst area)","Zone 7 (Miramichi area)"],
    "Newfoundland and Labrador": ["Central","Eastern","Labrador-Grenfell","Western"],
    "Nova Scotia":["Zone 1 - Western","Zone 2 - Northern","Zone 3 - Eastern","Zone 4 - Central"],
    "Nunavut": ["Nunavut"], "Northwest Territories": ["NWT"], "Ontario": ["Algoma","Brant","Chatham-Kent","Durham","Eastern",
                "Grey Bruce","Haldimand-Norfolk","Haliburton Kawartha Pineridge","Halton","Hamilton","Hastings Prince Edward",
                "Huron Perth","Kingston Frontenac Lennox & Addington","Lambton","Leeds Grenville and Lanark","Middlesex-London",
                "Niagara","North Bay Parry Sound","Northwestern","Ottawa","Peel","Peterborough","Porcupine",
                "Renfrew","Simcoe Muskoka","Southwestern","Sudbury","Thunder Bay","Timiskaming","Toronto","Waterloo",
                "Wellington Dufferin Guelph","Windsor-Essex","York"], "Prince Edward Island": ["Prince Edward Island"],
    "Quebec": ["Abitibi-Témiscamingue","Bas-Saint-Laurent","Capitale-Nationale",
                  "Chaudière-Appalaches","Côte-Nord","Estrie","Gaspésie-Îles-de-la-Madeleine",
                  "Lanaudière","Laurentides","Laval","Mauricie","Montérégie",
                  "Montréal","Nord-du-Québec","Nunavik",
                  "Outaouais","Saguenay","Terres-Cries-de-la-Baie-James"],
    "Saskatchewan":["Central","Far North","North","Regina","Saskatoon","South"],
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
                        # html.Div(children="Daily Mortality", className="options-header"),
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
                        html.Div(
                            children=[
                                html.Div(children="Sub-Region", className="dropdown-title"),
                                dcc.Dropdown(
                                    id='subregion-dropdown',
                                    className='dropdown',
                                    value = 'Waterloo'
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
                                    start_date="2020-03-13", #df_mort.date_death_report.min().date(),
                                    end_date="2021-03-31" #df_mort.date_death_report.max().date(),
                                ),
                            ]
                        ),
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
                                        100: '100%'
                                    },
                                    # handleLabel={"showCurrentValue": True,"label": "VALUE"},
                                ),
                                # html.Div(className='slider-output-container', id='slider-drag-output'),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Div(
                                    children="New Social Mobility vs Baseline",
                                    className="dropdown-title"
                                    ),
                                dcc.Slider(
                                    id='mobility-slider',
                                    min=0,
                                    max=100,
                                    step=1,
                                    value=100,
                                    marks={
                                        0: '-100% (total lockdown)',
                                        100: '0% (normal activity)'
                                    },
                                ),
                            ]
                        ),
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
                                        100: '100%'
                                    },
                                ),
                            ]
                        ),
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
                                    value=3, # todo: change back to 1
                                    marks={
                                        0: '0 mo',
                                        # 1: '1 mo',
                                        2: '2 mo',
                                        # 3: '3 mo',
                                        4: '4 mo',
                                        # 5: '5 mo',
                                        6: '6 mo',
                                        # 7: '7 mo',
                                        8: '8 mo',
                                        # 9: '9 mo',
                                        10: '10 mo',
                                        # 11: '11 mo',
                                        12: '1 yr'
                                    },
                                ),
                            ]
                        ),
                        # html.Div(
                        #     children= [
                        #         dcc.Graph(
                        #             id="data-chart", config={"displayModeBar": False},
                        #         ),
                        #     ],
                        #     className="card",
                        # ),
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
                        html.Div(
                            children=dcc.Graph(
                                id="simulation-chart", config={"displayModeBar": False},
                            ),
                            className="card",
                        ),
                        html.Div(
                            children= [
                                # dcc.Graph(
                                #     id="covid-chart", config={"displayModeBar": False}, style={'display': 'inline-block'},
                                # ),
                                dcc.Graph(
                                    id="cases-chart", config={"displayModeBar": False}, # style={'display': 'inline-block'},
                                ),
                            ],
                            # className="card",
                        ),
                        # html.Div(
                        #     children=dcc.Graph(
                        #         id="cases-chart", config={"displayModeBar": False},
                        #     ),
                        #     className="card",
                        # ),
                        html.Div(
                            children= [
                                dcc.Graph(
                                    id="mobility-chart", config={"displayModeBar": False}, # style={'display': 'inline-block'},
                                ),
                                dcc.Graph(
                                    id="weather-chart", config={"displayModeBar": False}, # style={'display': 'inline-block'},
                                ),
                                dcc.Graph(
                                    id="vaccination-chart", config={"displayModeBar": False}, # style={'display': 'inline-block'},
                                ),
                            ],
                            # className="card",
                        ),
                        # html.Div(
                        #     children=[
                        #         dcc.Graph(
                        #             id="map1", config={"displayModeBar": False},
                        #         ),
                        #         dcc.Graph(
                        #             id="map2", config={"displayModeBar": False},
                        #         ),
                        #     ],
                        #     className="card",
                        # ),
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

def display_info_box(btn_click):
    if (btn_click % 2) == 1:
        return dedent(extend_intro), "Close"
    else:
        return dedent(base_intro), "Learn More"


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
        Input('forecast-slider', 'value'),
        Input('facemask-slider', 'value'),
        Input('mobility-slider', 'value'),
        Input('vaccine-slider', 'value'),
    ],
)
def update_forecast_chart(province_name, region, start_date, end_date, days_to_forecast, facemask, xMob, vac):
    province_name = update_province_name(province_name)

    # ============== SIMULATION GRAPH ==============
    print("vac val before division: " + str(vac))
    
    xMob = -100 + xMob
    facemask = facemask * 70 / 100
    vac = vac / 100.0

    print("fm val: " + str(facemask))
    print("vac val: " + str(vac))

    pred_fig = go.Figure()
    pred_fig.add_trace(go.Scatter(
        x=date(province_name, region, start_date, end_date),
        y=r_avg(province_name, region, start_date, end_date),
        name='Previous Deaths',
    ))
    for i in range(10):
        pred_fig.add_trace(go.Scatter(
            x=predicted_dates(province_name, region, start_date, end_date, days_to_forecast),
            y=predicted_deaths(province_name, region, start_date, end_date, days_to_forecast, xMob, facemask, vac),
            name='Predicted Deaths',
        ))
    updatemenus = [
        dict(
            type="buttons",
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


    pred_fig.update_layout(title='Daily Predicted Deaths in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Daily Mortality (7-day Rolling Average)',
                   updatemenus=updatemenus)


    return pred_fig

@app.callback(
    Output("weather-chart", "figure"),
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input('forecast-slider', 'value'),
    ],
)
def update_weather_chart(province_name, region, start_date, end_date, forecasted_dates):
    # ============== WEATHER GRAPH ==============
    temp_files = get_temp_files(province_name, region, start_date, end_date)
    temp_dates = get_temp_dates(temp_files)
    temp_vals = get_temp_vals(temp_files)

    new_dates = predicted_dates(province_name, region, start_date, end_date, forecasted_dates)

    # temp_files = get_temp_files(province_name, region, start_date, end_date)
    data = {'Date':  get_temp_dates(temp_files),
        'Mean Temperature': get_temp_vals(temp_files)}
    forecasted = datetime.timedelta(days=forecasted_dates)

    weather_fig = px.line(df_mort, x = temp_dates, y = temp_vals)
    weather_fig.update_layout(title='Daily Reported Temperature in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Mean Temperature')
    weather_fig.add_trace(go.Scatter(
            x=new_dates,
            y=avg_temp_data(current_date, current_date + forecasted, data),
            name='Average Temp in Last 5 Years',
        ))
    
    return weather_fig

@app.callback(
    Output("cases-chart", "figure"), # Output("map1", "figure"), Output("map2", "figure")],
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_cases_charts(province_name, region, start_date, end_date):
    province_name = update_province_name(province_name)

    # ============== CASES GRAPH ==============
    cases_fig = px.line(df_mort, x = date_cases(province_name, region, start_date, end_date), y = ravg_cases(province_name, region, start_date, end_date))
    cases_fig.update_layout(title='Daily Reported Cases in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Daily Cases (7-day Rolling Average)')

    # ============== MAP ==============

    # map_fig = go.Figure(go.Scattermapbox(
    # fill = "toself",
    # lon = [-74, -70, -70, -74], lat = [47, 47, 45, 45],
    # marker = { 'size': 10, 'color': "orange" }))

    # map_fig.update_layout(
    #     mapbox = {
    #         'style': "stamen-terrain",
    #         'center': {'lon': -73, 'lat': 46 },
    #         'zoom': 5},
    #     showlegend = False)

    # df_test = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/fips-unemp-16.csv",
    #                dtype={"fips": str})

    # fig = px.choropleth(df_test, locations='fips', color='unemp',
    #                        color_continuous_scale="Viridis",
    #                        range_color=(0, 12),
    #                        scope="usa",
    #                        labels={'unemp':'unemployment rate'}
    #                       )
    # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})


    return cases_fig #, map_fig, fig

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
    xMob = -100 + xMob
    dates = predicted_dates(province_name, region, start_date, end_date, forecasted_dates)
    mob_values = []
    for i in range(len(dates)):
        mob_values.append(xMob)

     # ============== MOBILITY GRAPH ==============
    mobility_fig = px.line(df_mort, x = date_mob(province_name, region, start_date, end_date), y = mobility(province_name, region, start_date, end_date))
    mobility_fig.update_layout(title='Social Mobility in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Social Mobility')
    mobility_fig.add_trace(go.Scatter(
            x=dates,
            y=mob_values,
            name='Simulated Mobility',
        ))

    return mobility_fig

@app.callback(
    Output("vaccination-chart", "figure"),
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
    ],
)

def update_vaccination_charts(province_name, region):
    province_name = update_province_name(province_name)

    # ============== VACCINATION GRAPH ==============
    vaccination_fig = px.line(df_vaccinations(province_name, region), x = df_vaccinations(province_name, region).date, y = df_vaccinations(province_name, region).total_vaccinations)
    vaccination_fig.update_layout(title='Fraction of the Population Vaccinated in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Total Vaccinations/Population of Region')

    return vaccination_fig
    
# @app.callback(
#     Output("data-chart", "figure"),
#     [
#         Input("region-dropdown", "value"),
#         Input("subregion-dropdown", "value"),
#     ],
# )
# def update_table(province_name, region_name):
    # data_headers = ["Land Area", "Total Population", "Fraction of Population > 80 yrs", "PWPD", "Average number / house"]
    # data_values = [get_land_area(province_name, region_name), get_total_pop(province_name, region_name), get_frac_pop_over_80(province_name, region_name), get_pwpd(province_name, region_name), get_avg_house(province_name, region_name)]
    # fig = go.Figure(
    #     data=[go.Table(header=dict(values=['Category', 'Value']),
    #         cells=dict(values=[data_headers, data_values]))]
    #     )
    # return fig


# -------------- STATIC DATA HELPER FUNCTIONS --------------

def get_region_info(province_name, region_name):
    prov_info = static_data[static_data.province_name == province_name]
    region_info = prov_info[prov_info.health_region == region_name]
    return region_info

def get_avg_house(province_name, region_name):
    return get_region_info(province_name, region_name).house.item()

def get_land_area(province_name, region_name):
    land_area = get_region_info(province_name, region_name).landarea.item()
    return land_area

def get_total_pop(province_name, region_name):
    total_pop = get_region_info(province_name, region_name).total_pop.item()
    return total_pop

def get_ann_death(province_name, region_name):
    annDeath = get_region_info(province_name, region_name).anndeath.item()
    print("ANNUAL DEATH FOR: " + region_name + " = " + str(annDeath))
    return annDeath

def get_frac_pop_over_80(province_name, region_name):
    frac_over_80 = get_region_info(province_name, region_name).pop80.item()
    return frac_over_80 / get_total_pop(province_name, region_name)

def get_pwpd(province_name, region_name):
    pwpd = get_region_info(province_name, region_name).pwpd.item()
    return pwpd

def get_uid(province_name, region_name):
    uid = get_region_info(province_name, region_name).hr_uid.item()
    return uid

def get_prov_pop(province_name, region_name):
    prov_pop = get_region_info(province_name, region_name).prov_pop.item()
    return prov_pop

def get_past_temp(province_name, region_name, end_date):
    # temperature? -> temperature from when? -> avg temp from 42-14 days ago (1.5months - 2 weeks ago), take mean from past 5 years if too far in the future
    # 42 - 14 days ago
    # if 12 days ago > end_date (no past data for this date), then get historical average
    #else:

    return 12

# -------------- PREDICTIVE MODEL HELPER FUNCTIONS --------------

def predicted_dates(province_name, region_name, start_date, end_date, days_to_forecast):
    base = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    add_dates = [base + datetime.timedelta(days=x) for x in range(days_to_forecast * 30)]

    for i in range(len(add_dates)):
        add_dates[i] = datetime.datetime.strptime(str(add_dates[i]), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
    
    return add_dates

def predicted_deaths(province_name, region_name, start_date, end_date, days_to_forecast, xMob, facemask_val, vac_val):
    base = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    add_dates = [base + datetime.timedelta(days=x) for x in range(days_to_forecast * 30)]
    yVals = []
    global total_deaths

    # print("fm val: " + str(facemask_val))
    # print("vac val: " + str(vac_val))

    set_total_deaths(province_name, region_name, start_date, end_date)
    # uncertainty lambda: Sqrt[0.092/(14+Death in Past two weeks)]
    # add random gaussian number and show 10
    # add log graph (swtich back and forth) -> should be built in

    # t = r_avg(province_name, region_name, start_date, end_date)
    annDeath = get_ann_death(province_name, region_name) # 4234 # todo:
    tau = 25.1009
    lS0 = -2.70768
    trend1=-0.0311442
    xTrends1 = facemask_val # todo: Google Trends for face mask
    dtrends= 0.00722183
    xTemp = get_past_temp(province_name, region_name, end_date)
    Tmin2 = 24.6497
    dT2 = 0.00562779
    dT3 = 0.000182757
    xLogPWPD = math.log(get_pwpd(province_name, region_name) * get_frac_pop_over_80(province_name, region_name), 10) # Log10[PWD*AgreFrac[>80]] -> base 10
    H0 = 2.30833
    H2 = 5.89094
    Anl = -0.007345
    xHouse = get_avg_house(province_name, region_name) # Average number of people/household
    house2 = 0.0198985
    # xMob = -30 # get_mob(province_name, region_name, start_date) # todo: Google Workplace Mobility -> get from slider
    mob1 = 0.0379239
    v2 = 0  
    v1 = 0 # Fraction of vaccinated population (unto a month ago) -> time frame?
    # xVax1 = vac_val # Fraction of vaccinated population (unto a month ago) -> time frame? -> slider value
    v1= 11.9697
    xBeta = math.log(get_total_pop(province_name, region_name) / (get_pwpd(province_name, region_name) * get_land_area(province_name, region_name))) / math.log(0.25**2/get_land_area(province_name, region_name)) #get_total_pop(province_name, region_name) / get_land_area(province_name, region_name) # Population Sparsity
    # Daily Cases Tomorrow = Exp[lambda]*Daily cases today -> lambda

    # Vaccination data:
    Vax1 = vac_val # slider value
    Vax2 = 0
    # Exp? -> Exponential
    first = True
    deaths_tomorrow = 0
    deaths_today = last_mort
    total_deaths_2_months_prior = get_total_deaths_2_months_prior(province_name, region_name, end_date)
    # total_deaths_2_weeks_prior = get_total_deaths_2_weeks_prior(province_name, region_name, end_date)

    for i in range(len(add_dates)):
        xAnnual = math.log(annDeath, 10) # Log10[Annual Death] -> calendar year
        if (first == False):
            xHerd = total_deaths / annDeath  #Total Covid Death/Annual Death -> Annual death as in 2021
            if (i <= 60):
                xHerd2 = total_deaths_2_months_prior / annDeath # Total Covid Death (more than 2 months ago)/Annual Death -> what does more than 2 months ago mean? 2 months prior
            else:
                deaths_2_months = total_deaths_2_months_prior
                prior = i - 60
                prior_2_months = yVals[0:prior]
                for j in range(len(prior_2_months)):
                    deaths_2_months += prior_2_months[j]
                xHerd2 = deaths_2_months / annDeath
            print("\n")
            if (i < 14):
                prior = 14 - i
                deaths_2_weeks = get_total_deaths_2_weeks_prior(province_name, region_name, prior)
                for j in range(len(yVals)):
                    deaths_2_weeks += yVals[j]
            else:
                deaths_2_weeks = 0
                prior_2_weeks = yVals[-14:]
                for j in range(len(prior_2_weeks)):
                    deaths_2_weeks += prior_2_weeks[j]
            
            sigma = math.sqrt(0.092/(14+deaths_2_weeks))

            print("deaths 2 weeks: " + str(deaths_2_weeks))
            print("sigma: " + str(sigma))

            lambda_ = math.exp(.5*(lS0 + math.log(10)*xLogPWPD + math.log(0.25) +
                    2/(4 - xBeta)*math.log((2 - xBeta/2)/(2*10**xLogPWPD*.25**2)) - 
                    H0*xHerd - H2*(xHerd - xHerd2)*6 - v1*Vax1 + mob1*xMob + 
                    trend1*xTrends1 + dT2*(xTemp - Tmin2)**2.0 + dT3*(xTemp - Tmin2)**3.0 -
                    math.log(tau))) - 1/tau + house2*(xHouse - 2.75) + Anl*(xAnnual - 3.65) - v2*Vax2
            print("lambda before: " + str(lambda_))
            lambda_ += random.gauss(0, sigma) # Sqrt[0.092/(14 + Death in Past two weeks)
            print("lambda after: " + str(lambda_))
            deaths_tomorrow = math.exp(lambda_) * deaths_today
            # deaths_tomorrow += random.uniform(-0.01,0.1)
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

    
    return yVals

# -------------- MORTALITY HELPER FUNCTIONS --------------

def date(province_name, region_name, start_date, end_date):
    start_date_str = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_str = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')

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

def r_avg(province_name, region_name, start_date, end_date):
    start_date_str = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date_str = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')

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

    global last_mort
    last_mort = vals1[-1]
    
    return vals1

def get_total_deaths_this_year(province_name, region_name, end_date):
    first_day = "13-03-2020" # df_mort.date_death_report.min().date().strftime('%d-%m-%Y')
    first_day_this_year = "01-01-" + current_date.strftime("%Y") #datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    today = current_date.strftime('%d-%m-%Y')

    df_this_year = df_mort[df_mort.date_death_report.between(
        first_day_this_year, today
    )]
    df_province_this_year = df_this_year[df_this_year.province == province_name]
    deaths_this_year = df_province_this_year.deaths[df_province_this_year.health_region == region_name]

    total_deaths_this_year = 0 # reset total deaths

    for d in deaths_this_year:
        total_deaths_this_year += d

    return total_deaths_this_year

def get_total_deaths_2_months_prior(province_name, region_name, end_date):
    first_day = "13-03-2020" # df_mort.date_death_report.min().date().strftime('%d-%m-%Y')

    delta_2_months = datetime.timedelta(days=60)
    end_date_2_months_ago = current_date - delta_2_months
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

def get_total_deaths_2_weeks_prior(province_name, region_name, days_prior):
    delta = datetime.timedelta(days=days_prior)
    first_day = current_date - delta
    first_day = first_day.strftime('%d-%m-%Y')
    end_date_2_weeks_ago = current_date

    df_2_weeks = df_mort[df_mort.date_death_report.between(
        first_day, end_date_2_weeks_ago
    )]
    df_province_2_weeks = df_2_weeks[df_2_weeks.province == province_name]
    deaths_2_weeks = df_province_2_weeks.deaths[df_province_2_weeks.health_region == region_name]

    total_deaths_2_weeks = 0.0 # reset total deaths

    for d in deaths_2_weeks:
        total_deaths_2_weeks += d

    # print("2 weeks function: " + str(total_deaths_2_weeks))
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

    # print('TOTAL DEATHS: ' + str(total_deaths))

# -------------- CASES HELPER FUNCTIONS --------------

def date_cases(province_name, region_name, start_date, end_date):
    filtered_df = df_cases[df_cases.date_report.between(
        datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y'),
        datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    )]
    dfcases_province = filtered_df[filtered_df.province == province_name]
    return dfcases_province.date_report[dfcases_province.health_region == region_name]

def ravg_cases(province_name, region_name, start_date, end_date):
    filtered_df = df_cases[df_cases.date_report.between(
        datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y'),
        datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    )]
    dfcases_province = filtered_df[filtered_df.province == province_name]
    return dfcases_province.cases[dfcases_province.health_region == region_name].rolling(window=7).mean()

# -------------- MOBILITY HELPER FUNCTIONS --------------
def mobility(province_name, region_name, start_date, end_date):

    filtered_df = mobility_info[mobility_info.date.between(
        start_date, end_date
        # datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y'),
        # datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    )]
    
    weat_info_province = static_data[static_data.province_name == province_name]
    sub_region = weat_info_province.sub_region_2[weat_info_province.health_region == region_name].item()

    return filtered_df.workplaces_percent_change_from_baseline[mobility_info.sub_region_2 == sub_region].rolling(window=7).mean()

def date_mob(province_name, region_name, start_date, end_date):

    filtered_df = mobility_info[mobility_info.date.between(
        start_date, end_date
        # datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y'),
        # datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    )]
    
    weat_info_province = static_data[static_data.province_name == province_name]
    sub_region = weat_info_province.sub_region_2[weat_info_province.health_region == region_name].item()
    
    return filtered_df.date[mobility_info.sub_region_2 == sub_region]

# -------------- WEATHER HELPER FUNCTIONS --------------

def get_temp_dates(temp_files):
    dates = []
    for file in temp_files:
        # print (file)
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

        gloabl_date = str(year) + "-" + month 
        target_url = weather_base_url + prov_id + '/climate_daily_' + prov_id + '_' + climate_id + '_' + gloabl_date + '_P1D.csv'
        temp_files.append(target_url)

    return temp_files

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
    return df_weat_date

# -------------- VACCINATION HELPER FUNCTIONS --------------

def vaccination_data(province_name, region_name):

    if province_name == 'Alberta':
        api = vac_base_url_prov + str(provinceid(province_name, region_name))   
        response = requests.get(api)
        api_data = response.json()["data"]
    
    elif province_name == 'New Brunswick':
        api = vac_base_url_prov + str(provinceid(province_name, region_name))   
        response = requests.get(api)
        api_data = response.json()["data"]
    
    elif province_name == 'NL':
        api = vac_base_url_prov + str(provinceid(province_name, region_name))   
        response = requests.get(api)
        api_data = response.json()["data"]
        
    elif province_name == 'Nova Scotia':
        api = vac_base_url_prov + str(provinceid(province_name, region_name))   
        response = requests.get(api)
        api_data = response.json()["data"]    
    
    else:
        api = vac_base_url + str(get_uid(province_name, region_name))   
        response = requests.get(api)
        api_data = response.json()["data"]
    
    return api_data

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

def vac_df_data(province_name, region_name):
    vac_data = {'date':  get_vaccination_dates(province_name, region_name),
        'total_vaccinations': get_vaccination_vals(province_name, region_name)}
    return vac_data

def df_vaccinations(province_name, region_name):
    
    if province_name == 'Alberta':
        df_vaccinations = pd.DataFrame(vac_df_data(province_name, region_name), columns = ['date','total_vaccinations'])
        df_vaccinations = df_vaccinations.dropna()
        df_vaccinations['total_vaccinations'] = df_vaccinations.total_vaccinations.div(get_prov_pop(province_name, region_name))
    
    elif province_name == 'New Brunswick':
        df_vaccinations = pd.DataFrame(vac_df_data(province_name, region_name), columns = ['date','total_vaccinations'])
        df_vaccinations = df_vaccinations.dropna()
        df_vaccinations['total_vaccinations'] = df_vaccinations.total_vaccinations.div(get_prov_pop(province_name, region_name))
        
    elif province_name == 'NL':
        df_vaccinations = pd.DataFrame(vac_df_data(province_name, region_name), columns = ['date','total_vaccinations'])
        df_vaccinations = df_vaccinations.dropna()
        df_vaccinations['total_vaccinations'] = df_vaccinations.total_vaccinations.div(get_prov_pop(province_name, region_name))
        
    elif province_name == 'Nova Scotia':
        df_vaccinations = pd.DataFrame(vac_df_data(province_name, region_name), columns = ['date','total_vaccinations'])
        df_vaccinations = df_vaccinations.dropna()
        df_vaccinations['total_vaccinations'] = df_vaccinations.total_vaccinations.div(get_prov_pop(province_name, region_name))
    
    else:
        df_vaccinations = pd.DataFrame(vac_df_data(province_name, region_name), columns = ['date','total_vaccinations'])
        df_vaccinations = df_vaccinations.dropna()
        df_vaccinations['total_vaccinations'] = df_vaccinations.total_vaccinations.div(get_total_pop(province_name, region_name))
    
    return df_vaccinations

def get_frac_vaccinations_1_month_prior(province_name, region_name):
    
    current_date = datetime.datetime.now() #datetime.datetime.now()
    first_day = df_vaccinations(province_name, region_name).date.min()
    
    delta_1_month = datetime.timedelta(days=30)
    end_date_1_month_ago = current_date - delta_1_month
    end_date_1_month_ago = end_date_1_month_ago.strftime('%Y-%m-%d')
    
    df = df_vaccinations(province_name, region_name)
    
    df_1_month = df[df.date.between(
    first_day, end_date_1_month_ago
    )]

    return df_1_month.mean().item()

#def get_frac_vaccinations_2_weeks_prior(province_name, region_name, days_prior):
    
    #current_date = datetime.datetime.now() #datetime.datetime.now()
    #delta = datetime.timedelta(days=days_prior)
    #first_day = current_date - delta
    #first_day = first_day.strftime('%d-%m-%Y')
    #end_date_2_weeks_ago = current_date

    #df = df_vaccinations(province_name, region_name)
    
    #df_2_weeks = df[df.date.between(
    #    first_day, end_date_2_weeks_ago
    #)]
    
    #return df_2_weeks

if __name__ == "__main__":
    app.run_server(debug=True)

