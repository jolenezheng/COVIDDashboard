import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import numpy as np
import json
import plotly.express as px

# Reads the JSON file
with open('data/health_regions.json', 'r') as myfile:
    data = myfile.read()

# Parses the file
geo_json_data = json.loads(data)

import pandas as pd
df_mort = pd.read_csv(r'data/mortality2.csv', dtype={"ENG_LABEL": str})
df_mort["date_death_report"] = pd.to_datetime(df_mort["date_death_report"], format="%d-%m-%Y")

index = df_mort[df_mort['ENG_LABEL'] == 'Not Reported'].index
df_mort.drop(index, inplace=True)

df_latest_deaths = df_mort[df_mort['date_death_report'] == max(df_mort["date_death_report"])]
# print(df_latest_deaths)

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px

death_types = np.array(["deaths", "cumulative_deaths"])
death_types_label = 1

app = dash.Dash(__name__)

app.layout = html.Div([
    html.P("Cumulative Deaths or Latest Deaths:"),
    dcc.RadioItems(
        id='death_type', 
        options=[{'value': x, 'label': x} 
                 for x in death_types],
        value=death_types[0],
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Graph(id="choropleth"),
])

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

@app.callback(
    Output("choropleth", "figure"), 
    [Input("death_type", "value")])

def display_choropleth(death_type):
    if (death_type == 'deaths'):
        range_color = (0,10)
    else:
        range_color = (0, 500)
    fig = px.choropleth_mapbox(df_latest_deaths, geojson=geo_json_data, color=death_type,
                           color_continuous_scale="Deep", range_color=range_color, opacity=0.5,
                           locations="ENG_LABEL", featureidkey="properties.ENG_LABEL",
                           # projection='mercator',
                           height=500, center={"lat": 57.1304, "lon": -93.3468},
                           mapbox_style="carto-positron", zoom=3)

    return fig

app.run_server(debug=True)