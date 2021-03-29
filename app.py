# -*- coding: utf-8 -*-
import math
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
from dash.dependencies import Output, Input
import plotly.express as px
import plotly.graph_objects as go
import datetime as datetime

from textwrap import dedent

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


current_date = datetime.datetime.now()
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


# df_mob = pd.read_csv('https://www.gstatic.com/covid19/mobility/Global_Mobility_Report.csv')


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
    "Quebec": ["Abitibi-Témiscamingue","Bas-Saint-Laurent","Capitale-Nationale",
                  "Chaudière-Appalaches","Côte-Nord","Estrie","Gaspésie-Îles-de-la-Madeleine",
                  "Lanaudière","Laurentides","Laval","Mauricie","Montérégie",
                  "Montréal","Nord-du-Québec","Not Reported","Nunavik",
                  "Outaouais","Saguenay","Terres-Cries-de-la-Baie-James"],
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
                                    end_date=df_mort.date_death_report.max().date(),
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
                                    value=10,
                                    marks={
                                        0: '0%',
                                        100: '100%'
                                    },
                                    # handleLabel={"showCurrentValue": True,"label": "VALUE"},
                                ),
                                html.Div(className='slider-output-container', id='slider-drag-output'),
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
                                    value=10,
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
                                    children="Vaccination",
                                    className="dropdown-title"
                                    ),
                                dcc.Slider(
                                    id='vaccine-slider',
                                    min=0,
                                    max=100,
                                    step=1,
                                    value=10,
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
                                    value=1,
                                    marks={
                                        0: '0 days',
                                        1: '1 mo',
                                        2: '2 mo',
                                        3: '3 mo',
                                        4: '4 mo',
                                        5: '5 mo',
                                        6: '6 mo',
                                        7: '7 mo',
                                        8: '8 mo',
                                        9: '9 mo',
                                        10: '10 mo',
                                        11: '11 mo',
                                        12: '1 yr'
                                    },
                                ),
                            ]
                        ),
                        html.Div(
                            children= [
                                dcc.Graph(
                                    id="data-chart", config={"displayModeBar": False},
                                ),
                            ],
                            className="card",
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
                        html.Div(
                            children=dcc.Graph(
                                id="simulation-chart", config={"displayModeBar": False},
                            ),
                            className="card",
                        ),
                        html.Div(
                            children= [
                                dcc.Graph(
                                    id="covid-chart", config={"displayModeBar": False}, style={'display': 'inline-block'},
                                ),
                                dcc.Graph(
                                    id="cases-chart", config={"displayModeBar": False}, style={'display': 'inline-block'},
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
                                    id="mobility-chart", config={"displayModeBar": False}, style={'display': 'inline-block'},
                                ),
                                dcc.Graph(
                                    id="weather-chart", config={"displayModeBar": False}, style={'display': 'inline-block'},
                                ),
                            ],
                        #     # className="card",
                        ),
                        html.Div(
                            children=[
                                dcc.Graph(
                                    id="map1", config={"displayModeBar": False},
                                ),
                                dcc.Graph(
                                    id="map2", config={"displayModeBar": False},
                                ),
                            ],
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

def display_info_box(btn_click):
    if (btn_click % 2) == 1:
        return dedent(extend_intro), "Close"
    else:
        return dedent(base_intro), "Learn More"


 # ============== SLIDER CALLBACK ==============

@app.callback(Output('slider-drag-output', 'children'),
              [Input('facemask-slider', 'drag_value'), Input('facemask-slider', 'value')])
def display_value(drag_value, value):
    return 'For testing purposes: Drag Value: {} | Value: {}'.format(drag_value, value)

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
        Input('forecast-slider', 'drag_value'),
    ],
)
def update_forecast_chart(province_name, region, start_date, end_date, days_to_forecast):
    province_name = update_province_name(province_name)

    # ============== SIMULATION GRAPH ==============
    filtered_df2 = df_mort[df_mort.date_death_report.between(
        "01-02-21", "03-26-21"
    )]
    df_province = filtered_df2[filtered_df2.province == province_name]
    ans = df_province[df_province.health_region == region]

    pred_fig = go.Figure()
    pred_fig.add_trace(go.Scatter(
        x=date(province_name, region, start_date, end_date),
        y=r_avg(province_name, region, start_date, end_date),
        name='Previous Deaths',
    ))
    pred_fig.add_trace(go.Scatter(
        x=predicted_dates(province_name, region, start_date, end_date, days_to_forecast),
        y=predicted_deaths(province_name, region, start_date, end_date, days_to_forecast),
        name='Predicted Deaths',
    ))

    pred_fig.update_layout(title='Daily Predicted Deaths in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Daily Mortality (7-day Rolling Average)')

    return pred_fig

@app.callback(
    Output("weather-chart", "figure"),
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_weather_chart(province_name, region, start_date, end_date):
    # ============== WEATHER GRAPH ==============
    temp_files = get_temp_files(province_name, region, start_date, end_date)
    temp_dates = get_temp_dates(temp_files)
    temp_vals = get_temp_vals(temp_files)

    weather_fig = px.line(df_mort, x = temp_dates, y = temp_vals)
    weather_fig.update_layout(title='Daily Reported Temperature in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Mean Temperature')
    
    return weather_fig

@app.callback(
    [Output("covid-chart", "figure"), Output("cases-chart", "figure"), Output("mobility-chart", "figure"), Output("map1", "figure"), Output("map2", "figure")],
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(province_name, region, start_date, end_date):
    province_name = update_province_name(province_name)

    # ============== MORTALITY GRAPH ==============
    mort_fig = px.line(df_mort, x = date(province_name, region, start_date, end_date), y = r_avg(province_name, region, start_date, end_date))
    mort_fig.update_layout(title='Daily Reported Deaths in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Daily Mortality (7-day Rolling Average)')
    

    # ============== CASES GRAPH ==============
    cases_fig = px.line(df_mort, x = date_cases(province_name, region, start_date, end_date), y = ravg_cases(province_name, region, start_date, end_date))
    cases_fig.update_layout(title='Daily Reported Cases in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Daily Cases (7-day Rolling Average)')

     # ============== MOBILITY GRAPH ==============
    mobility_fig = px.line(df_mort, x = date_mob(province_name, region, start_date, end_date), y = mobility(province_name, region, start_date, end_date))
    mobility_fig.update_layout(title='Social Mobility in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Social Mobility')


    # ============== MAP ==============

    map_fig = go.Figure(go.Scattermapbox(
    fill = "toself",
    lon = [-74, -70, -70, -74], lat = [47, 47, 45, 45],
    marker = { 'size': 10, 'color': "orange" }))

    map_fig.update_layout(
        mapbox = {
            'style': "stamen-terrain",
            'center': {'lon': -73, 'lat': 46 },
            'zoom': 5},
        showlegend = False)

    df_test = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/fips-unemp-16.csv",
                   dtype={"fips": str})

    fig = px.choropleth(df_test, locations='fips', color='unemp',
                           color_continuous_scale="Viridis",
                           range_color=(0, 12),
                           scope="usa",
                           labels={'unemp':'unemployment rate'}
                          )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})


    return mort_fig, cases_fig, mobility_fig, map_fig, fig


@app.callback(
    Output("data-chart", "figure"),
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
    ],
)
def update_table(province_name, region_name):
    data_headers = ["Land Area", "Total Population", "Fraction of Population > 80 yrs", "PWPD", "Average number / house"]
    data_values = [get_land_area(province_name, region_name), get_total_pop(province_name, region_name), get_frac_pop_over_80(province_name, region_name), get_pwpd(province_name, region_name), get_avg_house(province_name, region_name)]
    fig = go.Figure(
        data=[go.Table(header=dict(values=['Category', 'Value']),
            cells=dict(values=[data_headers, data_values]))]
        )
    return fig


# -------------- STATIC DATA HELPER FUNCTIONS --------------

def get_region_info(province_name, region_name):
    prov_info = static_data[static_data.province_name == province_name]
    region_info = prov_info[prov_info.health_region == region_name]
    return region_info

def get_avg_house(province_name, region_name):
    avg_house = get_region_info(province_name, region_name).house.item()
    # avg_house = house_info.house[house_info.health_region == region_name].item()
    print (avg_house)
    return avg_house

def get_land_area(province_name, region_name):
    land_area = get_region_info(province_name, region_name).landarea.item()
    return land_area

def get_total_pop(province_name, region_name):
    total_pop = get_region_info(province_name, region_name).total_pop.item()
    return total_pop

def get_frac_pop_over_80(province_name, region_name):
    frac_over_80 = get_region_info(province_name, region_name).pop80.item()
    return frac_over_80

def get_pwpd(province_name, region_name):
    pwpd = get_region_info(province_name, region_name).pwpd.item()
    return pwpd

# -------------- PREDICTIVE MODEL HELPER FUNCTIONS --------------

def predicted_dates(province_name, region_name, start_date, end_date, days_to_forecast):
    base = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    add_dates = [base + datetime.timedelta(days=x) for x in range(days_to_forecast * 30)]

    for i in range(len(add_dates)):
        add_dates[i] = datetime.datetime.strptime(str(add_dates[i]), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')

    
    return add_dates

def predicted_deaths(province_name, region_name, start_date, end_date, days_to_forecast):
    base = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    add_dates = [base + datetime.timedelta(days=x) for x in range(days_to_forecast * 30)]
    yVals = []

    annDeath = 2000
    tau = 25.1009
    lS0 = -2.70768
    trend1=-0.0311442
    xTrends1 = 1 # Google Trends for face mask
    dtrends= 0.00722183
    xTemp = 15 # temperature? -> temperature from when? -> avg temp from 42-14 days ago (1.5months - 2 weeks ago), take mean from past 5 years if too far in the future
    Tmin2 = 24.6497
    dT2 = 0.00562779
    dT3 = 0.000182757
    xLogPWPD = 1 # Log10[PWD*AgreFrac[>80]] -> base 10
    xHerd = 7/2 # Total Covid Death/Annual Death -> Annual death as in 2021
    xHerd2 = 1/2 # Total Covid Death (more than 2 months ago)/Annual Death -> what does more than 2 months ago mean? 2 months prior
    H0 = 2.30833
    H2 = 5.89094
    xAnnual = math.log(annDeath, 10) # Log10[Annual Death] -> calendar year
    Anl = -0.007345
    xHouse = get_avg_house(province_name, region_name) # Average number of people/household
    house2 = 0.0198985
    xMob = -35 # Google Workplace Mobility -> given day, month, etc.?
    mob1 = 0.0379239
    v2 = 0
    v1 = 0.05 # Fraction of vaccinated population (unto a month ago) -> time frame?
    xVax1 = 0.05 # Fraction of vaccinated population (unto a month ago) -> time frame?
    v1= 11.9697
    xBeta = 4 # Population Sparsity
    # Daily Cases Tomorrow = Exp[lambda]*Daily cases today -> what is lambda? -> equation (2 weeks)

    # what is xVax1, Vax1, Vax2?
    Vax1 = 0
    Vax2 = 0
    # What is the base for the logs?
    # what is Exp? -> Exponential
    # How far should we predict for? -> e.g. have slider that decides how far to predict for, have a default of 1month?
    y = 3
    for i in range(len(add_dates)):
        add_dates[i] = datetime.datetime.strptime(str(add_dates[i]), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
        # y = math.exp(.5*(lS0 + math.log(10)*xLogPWPD + math.log(0.25) + #clarify log 0.25 and 10
        #  2/(4 - xBeta)*math.log((2 - xBeta/2)/(2*10^xLogPWPD*.25^2)) - 
        #  H0*xHerd - H2*(xHerd - xHerd2)*6 - v1*Vax1 + mob1*xMob + 
        #  trend1*xTrends1 + dT2*(xTemp - Tmin2)^2 + dT3*(xTemp - Tmin2)^3 -
        #   math.log(tau))) - 1/tau + house2*(xHouse - 2.75) + Anl*(xAnnual - 3.65) - v2*Vax2 # y = lambda
        # cases_today = 
        # PWD from email
        yVals.append(y)
        y = y + 0.05

    
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
    
    ans = df_province.deaths[df_province.health_region == region_name].rolling(window=7).mean()
    vals1 = []
    for key in ans:
        vals1.append(key)
    
    return vals1

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
        print (file)
        weat_data =  pd.read_csv(file, encoding='Latin-1')
        temp_dates = weat_data['Date/Time'].values
        dates.extend(temp_dates)

    return dates

def get_temp_vals(temp_files):
    temps = []
    # temps = np.arange(10)
    for file in temp_files:
        print (file)
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

    for i in range(num_months): # what if file doesn't exist
        year = start_date.year
        month = start_date.month + i
        if (month > 12):
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


if __name__ == "__main__":
    app.run_server(debug=True)

