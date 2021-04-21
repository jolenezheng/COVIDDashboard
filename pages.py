import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc

introduction_text = dcc.Markdown('''This portal provides resources and tools that could help individuals and policy makers with a scientific, balanced, and evidence-based approach to manage and navigate the COVID-19 Pandemic. It provides historical information, important demographics, and resulting stochastic forecasting for local counties (US) or Health Units (Canada), for adjustable **vaccination** and **face-mask usage** and **social mobility reduction** strategies. The model is simultaneously calibrated against more than 2500 distinct epidemics (over 100,000 reproduction number measurements), over the course of the COVID-19 pandemic.''')

faq1 = "We use the predicted exponential growth/decay rate of mortality from a simple compartmental (SEIR) model, but assume that the parameters of the model have deterministic universal dependencies on a series of ten static or dynamic conditions for every specific county/health region. The dependencies are then calibrated for the historical data on the epidemics and drivers. We only use COVID-19 confirmed mortality data, as the case numbers are dependent on testing policies and availability. Furthermore, we measure the error of the model based on the residuals of the best-fit model. The forecasts are stochastic simulations, based on the best-fit model and residuals, which can be tuned for different mitigation strategies."
faq2 = html.Div([
  "The model depends on a series of static and dynamic drivers.",
  "The static drivers are: ",
  html.Ol([
    html.Li("Population Weighted Population Density"),
    html.Li("Population Sparsity"),
    html.Li("Fraction of population above 80 years old"),
    html.Li("Total annual death"),
    html.Li("Average number of the members of the household")
  ]),
  "\nThe dynamic drivers are: ",
  html.Ol([
    html.Li("COVID-19 Epidemic history in the region"),
    html.Li("Workplace Google social mobility within the past month"),
    html.Li("Google Trends for searches for 'Face Mask'"),
    html.Li("Temperature within the past month"),
    html.Li("Vaccination history")
  ]),
  "While we have studied many other potential quantitative drivers of the COVID-19 spread, the above are the only ones that show independent significant correlation (for >10^5 data points in >2500 counties) and have detailed enough publicly available statistics. "
])
faq3 = html.Div(["Population weighted population density (PWPD) is the population-weighted average of population density within square cells of (250 m)^2 area. This is a more characteristic indicator of transmission probability, as it characterizes the number of different people one is likely to meet within their local vicinity. For more on how we measure PWPD for any geographical region, and their actual values, please check", html.A(" Ben Holder's GitHub page.", href="https://github.com/holderbp/pwpd", target="_blank")]) # "Ben Holder's GitHub page."
faq4 = "Population sparsity measures how fast the population density drops within a distance (or area), around a typical person. It varies between 0 (for a completely uniform region) and 1 (for a sparse population). We find that a more sparse population distribution slows down the growth of the COVID-19 epidemic. "
faq5 = "As we consider COVID-19 mortality as the most easily quantifiable burden of the pandemic, the model attempts to forecast the growth rate of COVID-19 mortality. Since the infection fatality ratio (IFR) is an exponentially growing function of age, the outbreaks in older communities are expected to have the most significant impact on mortality. We find that PWPD for the population older than 80-years old is the most significant predictor of the growth rate."
faq6 = html.Div([
  "It is believed that the vast majority of COVID-19 infections are caused by a small fraction of those infected, a.k.a. superspreaders. However, if a significant fraction of superspreaders are already infected during a local outbreak, then the growth rate of the epidemic will slow down, otherwise known as",
  html.A(" herd immunity, or herd effect", href="https://uwaterloo.ca/news/news/q-experts-problem-herd-immunity-and-covid-19", target="_blank"),
  ". While this is not a strategy to control the epidemic, it is an effect that needs to be accounted for, in order to have an accurate model. In our analysis, we find that the population of susceptible superspreaders can be best quantified in terms of the ratio of COVID-19 death to pre-covid annual death. In particular, there is a large dependence on COVID death in the past two months (short-term population immunity) and a smaller dependence on COVID death through the epidemic history (long-term population immunity)."
])
faq7 = "Vaccination can slow down the epidemic, by reducing the severity of a SARS-COV-2 infection (thus preventing death and IFR) and by slowing down the onward transmission of the virus (i.e. reducing the number of susceptibles). The impact of the former on mortality growth rate depends on the recent vaccination history (past month) while the latter depends on the cumulative vaccination (while their effect lasts). This is calibrated against current available data in the United States."
faq8 = "While counties or health regions are the smallest administrative divisions for which we have (easily accessible) public data, outbreaks are even more localized. The process of coarse-graining these outbreaks to county/region level can introduce a systematic shift in the mortality growth rate. Somewhat reminiscent of renormalization in effective field theories, we find a logarithmic dependence on annual death can best describe this coarse-graining effect."
faq9 = "Due to the frequent and efficient contacts within a household, the infection can easily be transmitted in between household members, which effectively prolongs the duration of any infection, slowing the recovery, even in lieu of community transmission. We find that the community recovery rate slows down by approximately 50% for every additional household member."
faq10 = html.Div([
  "Early in the onset of the COVID-19 pandemic, Google and Apple started tabulating the social mobility of communities based on the locations of Android and iOS smartphone users. For our analysis, we used the",
  html.A(" Google community mobility reports ", href="https://www.google.com/covid19/mobility/", target="_blank"),
  "for US counties and Canadain Health Units. The Google social mobility is based on the number of people who visit different types of locations in a given community, compared to a baseline defined in January 2020, and is measured in percentage. While there are 6 categories for this mobility: Retail & Recreation, Grocery & Pharmacy, Parks, Transit Stations, Workplaces, and Residential, we find that Workplace mobility to be the only significant driver of mortality growth at the local level. While other measures of mobility are correlated with Workplace mobility, their inclusion does not significantly increase the predictive power of the model."
])
faq11 = html.Div([
  "We use",
  html.A(" Google Trends ", href="https://trends.google.com/trends/?geo=US", target="_blank"),
  "data for 'Face Mask' internet searches as a proxy for face mask usage in a community. While this is not a perfect measure of actual face-mask usage, we find it to be significantly anti-correlated with mortality growth rate (p-value of 10^-4), and thus a reason measure of social distancing and/or facemask usage. "
])
faq12 = html.Div([
  "We find that the community transmission rate of the SARS-COV-2 virus can decrease by a factor of two, as the temperature increases from 5 C (41 F) to 26 C (79 F). A possible physical explanation for this could be the",
  html.A(" lifetime of respiratory droplets that increases at lower temperatures and humidities", href="https://www.biorxiv.org/content/10.1101/2020.10.16.341883v3", target="_blank"),
  ". However, it also could be due to the increased duration that people may spend outdoors in warmer climates (up to 26 C in the US), where transmission is minimal."
])
faq13 = html.Div([
  "You can find out more about our work at",
  html.A(" nafshordi.com/covid", href="https://nafshordi.com/covid/", target="_blank"),
])
faq14 = "No. One of us (Ben Holder) has significant experience in modeling in-host viral dynamics but the rest of us bring our expertise from other diverse backgrounds to provide a multidisciplinary approach to a significant global challenge. We have reached out to some epidemiologists, who have been understandably busy with other COVID-19 related projects. Unfortunately, the urgency of the current situation does not allow us to follow traditional routes for academic multidisciplinary collaboration. "
faq15 = "Yes. All our work, so far, has been on a voluntary basis, and we can use all the help and expertise that we can get!"



landing_page = html.Div([
    dbc.Row(dbc.Col(html.Div("Waterloo COVID-19 Forecast and Mitigation Portal"))),
    dbc.Row(dbc.Col(html.Div(introduction_text))),
    dbc.Row(
        [
            dbc.Col(html.Div("Canadian Dashboard")),
            dbc.Col(html.Div("USA Dashboard")),
        ]
    ),
])

old_navbar = html.Div(
            dbc.Navbar(
                [
                    html.A(
                        # Use row and col to control vertical alignment of logo / brand
                        dbc.Row(
                            [
                                dbc.Col(dbc.NavbarBrand("COVID-19 Canadian Dashboard", className="ml-2")),
                                dbc.Col(html.Img(src='assets/canadian_flag.png', height="20px")),
                            ],
                            align="center",
                            no_gutters=True,
                        ),
                        href="https://plot.ly",
                    ),
                    dbc.NavbarToggler(id="navbar-toggler"),
                ],
                color="dark",
                dark=True,
                sticky="top",
            ),
        )

introduction_page = html.Div([
    dbc.Row([dbc.Col(html.H3("My Local COVID: History, Forecast and Mitigation Portal"))], className="mb-4"),
    dbc.Row([dbc.Col(html.P(introduction_text))], className="mb-4"),
    dbc.Row([dbc.Col(html.P("Important Disclaimer: Forecasts are subject to model, systematic, and statistical uncertainties. In particular, the assumed efficacy of vaccines in the population remains tentative."))], className="mb-4"),
    dbc.Row([dbc.Col(html.P("Data Sources:"))]),
    html.Ol([
        html.Li(html.A("Mortality and Cases", href="https://github.com/ccodwg/Covid19Canada/tree/master/timeseries_hr", target="_blank")),
        html.Li(html.A("Weather Data", href="https://dd.weather.gc.ca/climate/observations/daily/csv/", target="_blank")),
        html.Li(html.A("Mobility Data", href="https://www.google.com/covid19/mobility/", target="_blank")),
        html.Li(html.A("Trends Data", href="https://trends.google.com/trends/?geo=Canada", target="_blank")),
        html.Li(html.A("Vaccination Data", href="https://api.covid19tracker.ca/docs/1.0/overview", target="_blank")),
    ]),
])

about_page = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(html.Div(html.H4("About Us"))),
            ],
            align="start",
        ),
        dbc.Row(
            [
                dbc.Col([
                  html.Div("Our Team is scattered across North America, but is headquartered at the University of Waterloo. You can reach us at", style={'display': 'inline-block'}),
                  html.A(": nafshordi@pitp.ca", href='https://plot.ly', target="_blank", style={'display': 'inline-block'}),
                ])
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Card([ 
                    dbc.CardHeader("Niayesh Afshordi"),
                    dbc.CardBody(
                        [
                            html.P(
                                "Associate Professor of Physics and Astronomy at the University of Waterloo and Associate Faculty in Cosmology at the Perimeter Institute for Theoretical Physics",
                                className="card-text",
                            ),
                        ]
                    ),
                ], color="danger", inverse=True)),
                dbc.Col(dbc.Card([ 
                    dbc.CardHeader("Mohammad Bahrami"),
                    dbc.CardBody(
                        [
                            html.P(
                                "Wolfram Research",
                                className="card-text",
                            ),
                        ]
                    ),
                ], color="warning", inverse=True)),
                dbc.Col(dbc.Card([ 
                    dbc.CardHeader("Elizabeth Gould"),
                    dbc.CardBody(
                        [
                            html.P(
                                "Postdoctoral Researcher at the Arthur B. McDonald Canadian Astroparticle Physics Research Institute",
                                className="card-text",
                            ),
                        ]
                    ),
                ], color="success", inverse=True)),
                dbc.Col(dbc.Card([ 
                    dbc.CardHeader("Benjamin Holder"),
                    dbc.CardBody(
                        [
                            html.P(
                                "Associate Professor of Physics at Grand Valley State University",
                                className="card-text",
                            ),
                        ]
                    ),
                ], color="primary", inverse=True)),
            ],
            align="end",
            className="mb-4"
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Card([ 
                    dbc.CardHeader("Shafika Olalekan Koiki"),
                    dbc.CardBody(
                        [
                            html.P(
                                "Undergraduate Student in Physics and Astronomy at the University of Waterloo",
                                className="card-text",
                            ),
                        ]
                    ),
                ], color="danger", inverse=True)),
                dbc.Col(dbc.Card([ 
                    dbc.CardHeader("Daniel Lichblau"),
                    dbc.CardBody(
                        [
                            html.P(
                                "Wolfram Research",
                                className="card-text",
                            ),
                        ]
                    ),
                ], color="warning", inverse=True)),
                dbc.Col(dbc.Card([ 
                    dbc.CardHeader("Steve Weinstein"),
                    dbc.CardBody(
                        [
                            html.P(
                                "Associate Professor of Philosophy at the University of Waterloo",
                                className="card-text",
                            ),
                        ]
                    ),
                ], color="success", inverse=True)),
                dbc.Col(dbc.Card([ 
                    dbc.CardHeader("Jolene Zheng"),
                    dbc.CardBody(
                        [
                            html.P(
                                "Undergraduate Student in Computer Science at the University of Waterloo",
                                className="card-text",
                            ),
                        ]
                    ),
                ], color="primary", inverse=True)),
            ],
            align="end",
            className="mb-4"
        ),
    ]
)

collapse = html.Div(
    [
        dbc.Button(
            "Open collapse",
            id="q1",
            className="mb-3",
            color="primary",
        ),
        dbc.Collapse(
            dbc.Card(dbc.CardBody("This content is hidden in the collapse")),
            id="a1",
        ),
    ]
)

faq_page2 = html.Div(
  [
    dbc.Row(html.Div(html.H4("Frequently Asked Questions"))),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "How does the model work?",
                        color="link",
                        id="q1",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq1),
                id="a1",
            ),
        ]
    ),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "What does the model depend on on?",
                        color="link",
                        id="q2",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq2),
                id="a2",
            ),
        ]
    ),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "What is Population Weighted Density (PWPD)?",
                        color="link",
                        id="q3",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq3),
                id="a3",
            ),
        ]
    ),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "What is Population Sparsity?",
                        color="link",
                        id="q4",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq4),
                id="a4",
            ),
        ]
    ),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "Why does the age distribution matter?",
                        color="link",
                        id="q5",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq5),
                id="a5",
            ),
        ]
    ),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "How does herd or population immunity enter the model?",
                        color="link",
                        id="q6",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq6),
                id="a6",
            ),
        ]
    ),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "How does vaccination enter the model?",
                        color="link",
                        id="q7",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq7),
                id="a7",
            ),
        ]
    ),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "Why does annual death matter?",
                        color="link",
                        id="q8",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq8),
                id="a8",
            ),
        ]
    ),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "How does the number of household members impact the epidemic?",
                        color="link",
                        id="q9",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq9),
                id="a9",
            ),
        ]
    ),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "What is Social Mobility and how does it impact the epidemic?",
                        color="link",
                        id="q10",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq10),
                id="a10",
            ),
        ]
    ),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "What is Social Mobility and how does it impact the epidemic?",
                        color="link",
                        id="q11",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq11),
                id="a11",
            ),
        ]
    ),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "Why does temperature impact COVID-19 spread?",
                        color="link",
                        id="q12",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq12),
                id="a12",
            ),
        ]
    ),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "Where can I read more?",
                        color="link",
                        id="q13",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq13),
                id="a13",
            ),
        ]
    ),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "Do you have an epidemiologist on your team?",
                        color="link",
                        id="q14",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq14),
                id="a14",
            ),
        ]
    ),
    dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        "Can I contribute to this work?",
                        color="link",
                        id="q15",
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(faq15),
                id="a15",
            ),
        ]
    ),
  ], className="accordion"
)


faq_page = html.Div([
    dbc.Row(html.Div("Frequently Asked Questions")),
    dbc.Row([
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "How does the model work?",
              id="q1",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq1)),
              id="a1",
            ),
          ]))
        ),
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "What does the model depend on on?",
              id="q2",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq2)),
              id="a2",
            ),
          ]))
        ),
    ]),
    dbc.Row([
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "What is Population Weighted Density (PWPD)?",
              id="q3",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq3)),
              id="a3",
            ),
          ]))
        ),
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "What is Population Sparsity?",
              id="q4",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq4)),
              id="a4",
            ),
          ]))
        ),
    ]),
    dbc.Row([
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "Why does the age distribution matter?",
              id="q5",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq5)),
              id="a5",
            ),
          ]))
        ),
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "How does herd or population immunity enter the model?",
              id="q6",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq6)),
              id="a6",
            ),
          ]))
        ),
    ]),
    dbc.Row([
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "How does vaccination enter the model?",
              id="q7",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq7)),
              id="a7",
            ),
          ]))
        ),
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "Why does annual death matter?",
              id="q8",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq8)),
              id="a8",
            ),
          ]))
        ),
    ]),
    dbc.Row([
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "How does the number of household members impact the epidemic?",
              id="q9",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq9)),
              id="a9",
            ),
          ]))
        ),
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "What is Social Mobility and how does it impact the epidemic?",
              id="q10",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq10)),
              id="a10",
            ),
          ]))
        ),
    ]),
    dbc.Row([
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "How do you measure face mask usage?",
              id="q11",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq11)),
              id="a11",
            ),
          ]))
        ),
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "Why does temperature impact COVID-19 spread?",
              id="q12",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq12)),
              id="a12",
            ),
          ]))
        ),
    ]),
    dbc.Row([
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "Where can I read more?",
              id="q13",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq13)),
              id="a13",
            ),
          ]))
        ),
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "Do you have an epidemiologist on your team?",
              id="q14",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq14)),
              id="a14",
            ),
          ]))
        ),
    ]),
    dbc.Row([
        dbc.Col(
          dbc.Row(html.Div([
            dbc.Button(
              "Can I contribute to this work?",
              id="q15",
              className="mb-3",
              color="primary",
            ),
            dbc.Collapse(
              dbc.Card(dbc.CardBody(faq15)),
              id="a15",
            ),
          ]))
        ),
    ]),
])

# dbc.Row([
#         dbc.Col(
#           dbc.Row(html.Div([
#             dbc.Button(
#               "How",
#               id="q1",
#               className="mb-3",
#               color="primary",
#             ),
#             dbc.Collapse(
#               dbc.Card(dbc.CardBody(faq1)),
#               id="a1",
#             ),
#           ]))
#         ),
#         dbc.Col(
#           dbc.Row(html.Div([
#             dbc.Button(
#               "How",
#               id="q1",
#               className="mb-3",
#               color="primary",
#             ),
#             dbc.Collapse(
#               dbc.Card(dbc.CardBody(faq1)),
#               id="a1",
#             ),
#           ]))
#         ),
#     ]),

# dbc.Row(html.Div([
#       dbc.Button(
#         "How",
#         id="q1",
#         className="mb-3",
#         color="primary",
#       ),
#       dbc.Collapse(
#         dbc.Card(dbc.CardBody(faq1)),
#         id="a1",
#       ),
#     ])),

base_intro = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, \
    sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. \
        Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris \
            nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor \
                in reprehenderit in voluptate velit esse cillum dolore eu \
                    fugiat nulla pariatur. Excepteur sint occaecat cupidatat \
                        non proident, sunt in culpa qui officia deserunt mollit \
                            anim id est laborum.
"""
