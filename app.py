# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
from dash.dependencies import Output, Input
import plotly.express as px
import plotly.graph_objects as go
import datetime as datetime

from textwrap import dedent


df_mort = pd.read_csv('https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_hr/mortality_timeseries_hr.csv')
df_mort["date_death_report"] = pd.to_datetime(df_mort["date_death_report"], format="%d-%m-%Y")

df_cases = pd.read_csv('https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_hr/cases_timeseries_hr.csv')

weather_base_url = 'https://dd.weather.gc.ca/climate/observations/daily/csv/'
weat_info = pd.read_csv('data/health_regions_weather.csv')

current_date = datetime.datetime.now()
gloabl_date = current_date.strftime('%Y-%m')

prov_id = "ON"
climate_id = 0
target_url = ""
weat_data = None
weat_city = None
date_city = None

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
                                id="covid-chart", config={"displayModeBar": False},
                            ),
                            className="card",
                        ),
                        html.Div(
                            children=dcc.Graph(
                                id="cases-chart", config={"displayModeBar": False},
                            ),
                            className="card",
                        ),
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

def display_info_box(btn_click):
    if (btn_click % 2) == 1:
        return dedent(extend_intro), "Close"
    else:
        return dedent(base_intro), "Learn More"


@app.callback(
    [Output("covid-chart", "figure"), Output("cases-chart", "figure"), Output("weather-chart", "figure")],
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(province_name, region, start_date, end_date):
    print(gloabl_date)
    # Update names to abbreviated form
    if (province_name == "Newfoundland and Labrador"):
        province_name = "NL"
    elif (province_name == "British Columbia"):
        province_name = "BC"
    elif (province_name == "Prince Edward Island"):
        province_name == "PEI"
    elif (province_name == "Northwest Territories"):
        province_name == "NWT"

    # ============== MORTALITY GRAPH ==============
    mort_fig = px.line(df_mort, x = date(province_name, region, start_date, end_date), y = r_avg(province_name, region, start_date, end_date))
    mort_fig.update_layout(title='Daily Reported Deaths in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Daily Mortality (7-day Rolling Average)')

    # ============== CASES GRAPH ==============
    cases_fig = px.line(df_mort, x = date_cases(province_name, region), y = ravg_cases(province_name, region))
    cases_fig.update_layout(title='Daily Reported Cases in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Daily Cases (7-day Rolling Average)')

    # ============== WEATHER GRAPH ==============
    colnames = ["x2","3x","xv","xvv",
                "Date/Time","y","m","d","Da","2a",
                "ac","asa","Mi","Mean Temp",
                "gf","hfgdgfd","adfgf",
                "Cos)","Co3lag","Totdm",
                "Tod","T2","Tfgf",
                "234rt","234","ff4rt434r",
                "Snow on Grnd Flag","Dir of Max Gust (10s deg)",
                "Dirf","Spff","Sp4"]

    prov_id = provinceid(province_name, region)
    climate_id = climateid(province_name, region)
    target_url = weather_base_url + prov_id + '/climate_daily_' + prov_id + '_' + climate_id + '_' + gloabl_date + '_P1D.csv'
    # weat_data =  pd.read_csv(target_url, names=colnames)
    # weat_data =  pd.read_csv(target_url, encoding='unicode_escape')
    # weat_city = weat_data.iloc[14]
    # weat_city = weat_data['Mean Temp (' + (u"\N{DEGREE SIGN}").decode('utf-8').strip() + '°C)']
    # weat_city = weat_data['Mean Temp']
    # weat_city = weat_data['Mean Temp (°C)']
    # weat_city = weat_data.columns[14]
    # weat_city =  pd.read_csv(target_url, usecols=[14]) #encoding='Latin-1')

    # weat_city = weat_data['Mean Temp (' + u"\u2103".encode('utf-8').strip() + 'C)']

    # date_city = weat_data['Date/Time']

    x = np.arange(10)

    weather_fig = px.line(df_mort, x = x, y = 2*x*x)
    weather_fig.update_layout(title='Daily Reported Temperature in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Mean Temperature')

    return mort_fig, cases_fig, weather_fig

# -------------- MORTALITY HELPER FUNCTIONS --------------
def date(province_name, region_name, start_date, end_date):

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    filtered_df = df_mort[df_mort.date_death_report.between(
        datetime.datetime.strftime(start_date, "%d-%m-%Y"),
        datetime.datetime.strftime(end_date, "%d-%m-%Y")
    )]
    
    df_province = filtered_df[filtered_df.province == province_name]
    return df_province.date_death_report[df_province.health_region == region_name]
    
def r_avg(province_name, region_name, start_date, end_date):

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    filtered_df = df_mort[df_mort.date_death_report.between(
        datetime.datetime.strftime(start_date, "%d-%m-%Y"),
        datetime.datetime.strftime(end_date, "%d-%m-%Y")
    )]
    
    df_province = filtered_df[filtered_df.province == province_name]
    return df_province.deaths[df_province.health_region == region_name].rolling(window=7).mean()


# -------------- WEATHER HELPER FUNCTIONS --------------

# Gets the climate ID for the health region
def climateid(province_name, region_name):
    weat_info_province = weat_info[weat_info.province_name == province_name]
    return weat_info_province.climate_id[weat_info_province.health_region == region_name].item()

# Gets the province abbreviation for the health region
def provinceid(province_name, region_name):
    weat_info_province = weat_info[weat_info.province_name == province_name]
    return weat_info_province.prov_id[weat_info_province.health_region == region_name].item()

# Gets the weather station name for the health region
def weatregion(province_name, region_name):
    weat_info_province = weat_info[weat_info.province_name == province_name]
    return weat_info_province.temp_region[weat_info_province.health_region == region_name].item()


# -------------- CASES HELPER FUNCTIONS --------------

def date_cases(province_name, region_name):
    dfcases_province = df_cases[df_cases.province == province_name]
    return dfcases_province.date_report[dfcases_province.health_region == region_name]

def ravg_cases(province_name, region_name):
    dfcases_province = df_cases[df_cases.province == province_name]
    return dfcases_province.cases[dfcases_province.health_region == region_name].rolling(window=7).mean()

if __name__ == "__main__":
    app.run_server(debug=True)

# {  {"", "Estimate", "Standard Error", "t\[Hyphen]Statistic",    "P\[Hyphen]Value"},  {tau, 25.1009, 1.69849, 14.7783, 2.28032*10^-49},  {lS0, -2.70768, 0.136775, -19.7966, 4.6873*10^-87},  {trend1, -0.0311442, 0.00722183, -4.31251, 0.0000161565},  {Tmin2, 24.6497, 1.02868, 23.9625, 1.56566*10^-126},  {dT2, 0.00562779, 0.00093845, 5.99689, 2.0182*10^-9},  {dT3, 0.000182757, 0.0000380385, 4.80453, 1.55338*10^-6},  {H0, 2.30833, 0.434351, 5.31443, 1.07219*10^-7},  {H2, 5.89094, 0.546897, 10.7716, 4.85314*10^-27},  {Anl, -0.007345, 0.00148539, -4.94485, 7.63276*10^-7},  {house2, 0.0198985, 0.0029732, 6.69261, 2.20381*10^-11},  {mob1, 0.0379239, 0.0033316, 11.3831, 5.29764*10^-30},  {v1, 20.1012, 10.8628, 1.85047, 0.0642483},  {v2, -0.0773693, 0.0664672, -1.16402, 0.244418} } 

# Exp[.5*(lS0(*ab*Log[10]*(xLogPWPD-1.96)*)(*+bb*(xBeta-0.187)*)+        Log[10]*xLogPWPD + Log[.25](*2/(4-xBeta)*bb+*)+        2/(4 - xBeta)*Log[(2 - xBeta/2)/(2*10^xLogPWPD*.25^2)] -        H0*xHerd - H2*(xHerd - xHerd2)*6 - v1*Vax1 + mob1*xMob +        trend1*xTrends1 + dT2*(xTemp - Tmin2)^2 +        dT3*(xTemp - Tmin2)^3 - Log[tau])] - 1/tau +    house2*(xHouse - 2.75) + Anl*(xAnnual - 3.65) -    v2*Vax2,(*2>ab>0&&*)-.2 < mob1 < .2 &&(*-2<mDec<2&&*)40 > tau > 10 &&    100 > H0 > -100 && 100 > H2 > -100 &&(*4>Timmune>1&&*)   4 > lS0 > -6 && -10 < trend1 < 10 &&    0 < Tmin2 < 30 && -.01 < dT2 < .01 && -.01 < dT3 < .01 && -5 <     house2 < 15 && -5 < Anl < 5 && -20 < v1 < 40 && -10 < v2 < 10}, {(*ab,*)tau, lS0, trend1, Tmin2, dT2, dT3, H0, H2, Anl, house2, mob1, \ v1, v2}, Flatten[{xLogPWPD, xBeta, xHerd, xHerd2, xAnnual, xHouse, xMob,    xTrends1, xTemp, Vax1, Vax2}



# Exp[.5*(lS0 + Log[10]*xLogPWPD + Log[.25] +        2/(4 - xBeta)*Log[(2 - xBeta/2)/(2*10^xLogPWPD*.25^2)] -        H0*xHerd - H2*(xHerd - xHerd2)*6 - v1*Vax1 + mob1*xMob +        trend1*xTrends1 + dT2*(xTemp - Tmin2)^2 +        dT3*(xTemp - Tmin2)^3 - Log[tau])] - 1/tau +    house2*(xHouse - 2.75) + Anl*(xAnnual - 3.65) -    v2*Vax2, -.2 < mob1 < .2 && 40 > tau > 10 && 100 > H0 > -100 &&    100 > H2 > -100 && 4 > lS0 > -6 && -10 < trend1 < 10 &&    0 < Tmin2 < 30 && -.01 < dT2 < .01 && -.01 < dT3 < .01 && -5 <     house2 < 15 && -5 < Anl < 5 && -20 < v1 < 40 && -10 < v2 < 10}, {tau, lS0, trend1, Tmin2, dT2, dT3, H0, H2, Anl, house2, mob1, v1, v2}, Flatten[{xLogPWPD, xBeta, xHerd, xHerd2, xAnnual, xHouse, xMob,    xTrends1, xTemp, Vax1, Vax2}


# Exp[.5*(lS0 + Log[10]*xLogPWPD + Log[.25] +       2/(4 - xBeta)*Log[(2 - xBeta/2)/(2*10^xLogPWPD*.25^2)] -       H0*xHerd - H2*(xHerd - xHerd2)*6 - v1*Vax1 + mob1*xMob +       trend1*xTrends1 + dT2*(xTemp - Tmin2)^2 + dT3*(xTemp - Tmin2)^3 -       Log[tau])] - 1/tau + house2*(xHouse - 2.75) +   Anl*(xAnnual - 3.65) - v2*Vax2