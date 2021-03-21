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


df_mort = pd.read_csv('https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_hr/mortality_timeseries_hr.csv', parse_dates=[0], dayfirst=True)
df_mort["date_death_report"] = pd.to_datetime(df_mort["date_death_report"], format="%d-%m-%Y", dayfirst =True)

df_cases = pd.read_csv('https://raw.githubusercontent.com/ccodwg/Covid19Canada/master/timeseries_hr/cases_timeseries_hr.csv')
df_cases["date_report"] = pd.to_datetime(df_cases["date_report"], format="%d-%m-%Y", dayfirst =True)

weather_base_url = 'https://dd.weather.gc.ca/climate/observations/daily/csv/'
weat_info = pd.read_csv(r'data/health_regions_weather.csv', encoding='Latin-1')

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
                                    children="Mobility",
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
                                    children="Vaccinations",
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
                                id="mobility-chart", config={"displayModeBar": False},
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


 # ============== SLIDER CALLBACK ==============

@app.callback(Output('slider-drag-output', 'children'),
              [Input('facemask-slider', 'drag_value'), Input('facemask-slider', 'value')])
def display_value(drag_value, value):
    return 'For testing purposes: Drag Value: {} | Value: {}'.format(drag_value, value)

@app.callback(
    [Output("covid-chart", "figure"), Output("cases-chart", "figure"), Output("mobility-chart", "figure"), Output("weather-chart", "figure")],
    [
        Input("region-dropdown", "value"),
        Input("subregion-dropdown", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(province_name, region, start_date, end_date):
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
    cases_fig = px.line(df_mort, x = date_cases(province_name, region, start_date, end_date), y = ravg_cases(province_name, region, start_date, end_date))
    cases_fig.update_layout(title='Daily Reported Cases in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Daily Cases (7-day Rolling Average)')

     # ============== MOBILITY GRAPH ==============
    mobility_fig = px.line(df_mort, x = date_mob(province_name, region, start_date, end_date), y = mobility(province_name, region, start_date, end_date))
    mobility_fig.update_layout(title='Social Mobility in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Social Mobility')

    # ============== WEATHER GRAPH ==============
    # colnames = ["x2","3x","xv","xvv",
    #             "Date/Time","y","m","d","Da","2a",
    #             "ac","asa","Mi","Mean Temp",
    #             "gf","hfgdgfd","adfgf",
    #             "Cos)","Co3lag","Totdm",
    #             "Tod","T2","Tfgf",
    #             "234rt","234","ff4rt434r",
    #             "Snow on Grnd Flag","Dir of Max Gust (10s deg)",
    #             "Dirf","Spff","Sp4"]

    prov_id = provinceid(province_name, region)
    climate_id = climateid(province_name, region)
    target_url = weather_base_url + prov_id + '/climate_daily_' + prov_id + '_' + climate_id + '_' + gloabl_date + '_P1D.csv'
    weat_data =  pd.read_csv(target_url, encoding='Latin-1')
    # weat_data =  pd.read_csv(target_url, names=colnames)
    # weat_data =  pd.read_csv(target_url, encoding='unicode_escape')
    # weat_city = weat_data.iloc[14]
    # weat_city = weat_data['Mean Temp (' + (u"\N{DEGREE SIGN}").decode('utf-8').strip() + '°C)']
    # weat_city = weat_data['Mean Temp']
    # weat_city = weat_data.columns[14]
    # weat_city =  pd.read_csv(target_url, usecols=[14]) #encoding='Latin-1')

    # weat_city = weat_data['Mean Temp (' + u"\u2103".encode('utf-8').strip() + 'C)']

    weat_city = weat_data['Mean Temp (°C)']
    date_city = weat_data['Date/Time']

    x = np.arange(10)
    # weat_city = x
    # date_city=2*x*x

    weather_fig = px.line(df_mort, x = date_city, y = weat_city)
    weather_fig.update_layout(title='Daily Reported Temperature in ' + region + ', ' + province_name,
                   xaxis_title='Date',
                   yaxis_title='Mean Temperature')

    return mort_fig, cases_fig, mobility_fig, weather_fig

# -------------- MORTALITY HELPER FUNCTIONS --------------
def date(province_name, region_name, start_date, end_date):
    # start_date = pd.to_datetime(start_date)
    # end_date = pd.to_datetime(end_date)
    # start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    # end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')

    # issue: python is treating d-m as m-d

    filtered_df = df_mort[df_mort.date_death_report.between(
        datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y'),
        datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        # start_date, end_date
    )]
    
    df_province = filtered_df[filtered_df.province == province_name]
    return df_province.date_death_report[df_province.health_region == region_name]
    
def r_avg(province_name, region_name, start_date, end_date):
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')

    filtered_df = df_mort[df_mort.date_death_report.between(
        start_date, end_date
    )]
    
    df_province = filtered_df[filtered_df.province == province_name]
    return df_province.deaths[df_province.health_region == region_name].rolling(window=7).mean()


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
    
    weat_info_province = weat_info[weat_info.province_name == province_name]
    sub_region = weat_info_province.sub_region_2[weat_info_province.health_region == region_name].item()

    return filtered_df.workplaces_percent_change_from_baseline[mobility_info.sub_region_2 == sub_region].rolling(window=7).mean()

def date_mob(province_name, region_name, start_date, end_date):

    filtered_df = mobility_info[mobility_info.date.between(
        start_date, end_date
        # datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y'),
        # datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    )]
    
    weat_info_province = weat_info[weat_info.province_name == province_name]
    sub_region = weat_info_province.sub_region_2[weat_info_province.health_region == region_name].item()
    
    return filtered_df.date[mobility_info.sub_region_2 == sub_region]

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


if __name__ == "__main__":
    app.run_server(debug=True)

