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
                    dbc.CardHeader(html.A("Niayesh Afshordi", href="mailto: nafshordi@uwaterloo.ca", target="_blank", style={"color": "white", "size":"14px"})),
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
                    dbc.CardHeader(html.A("Mohammad Bahrami", href="https://sites.google.com/site/mohbahrami/", target="_blank", style={"color": "white", "size":"14px"})),
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
                    dbc.CardHeader(html.A("Elizabeth Gould", href="mailto: quantumwarrior@gmail.com", target="_blank", style={"color": "white", "size":"14px"})),
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
                    dbc.CardHeader(html.A("Benjamin Holder", href="https://www.gvsu.edu/physics/dr-benjamin-holder-80.htm", target="_blank", style={"color": "white", "size":"14px"})),
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
                    dbc.CardHeader(html.A("Shafika Olalekan Koiki", href="mailto: solalekankoiki@uwaterloo.ca", target="_blank", style={"color": "white", "size":"14px"})),
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
                    dbc.CardHeader(html.A("Daniel Lichblau", href="mailto: danl@wolfram.com", target="_blank", style={"color": "white", "size":"14px"})),
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
                    dbc.CardHeader(html.A("Steve Weinstein", href="https://uwaterloo.ca/philosophy/people-profiles/steven-weinstein", target="_blank", style={"color": "white", "size":"14px"})),
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
                    dbc.CardHeader(html.A("Jolene Zheng", href="https://www.linkedin.com/in/jolenezheng/", target="_blank", style={"color": "white", "size":"14px"})),
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
                        "How do you measure face mask usage?",
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

initial_temp_vals = [1.2071428571428455, 1.1357142857142741, 0.97142857142856, 0.8571428571428458, 0.77142857142856, 0.4785714285714172, 0.07142857142856007, -0.11428571428572562, 0.1571428571428458, 0.08571428571427438, -0.10714285714286849, 0.02142857142856006, 0.007142857142845778, 0.19999999999998863, 0.44999999999998863, 0.564285714285703, 0.6499999999999887, 0.5571428571428458, 0.4785714285714172, 0.12857142857141723, 0.3857142857142744, 0.5928571428571315, 0.014285714285702926, -0.2785714285714399, -0.20000000000001134, -0.2714285714285828, -0.7642857142857257, -1.6785714285714397, -2.6500000000000115, -3.2642857142857253, -3.8928571428571535, -4.271428571428582, -4.5500000000000105, -4.442857142857153, -4.5500000000000105, -4.535714285714296, -4.485714285714296, -4.800000000000011, -5.4285714285714395, -5.721428571428582, -5.85000000000001, -5.628571428571439, -5.7285714285714375, -6.007142857142867, -6.05000000000001, -6.0357142857142945, -6.4142857142857235, -6.778571428571437, -7.1000000000000085, -7.235714285714294, -7.057142857142865, -6.757142857142865, -6.4142857142857235, -6.021428571428579, -5.428571428571437, -4.564285714285722, -4.128571428571436, -3.3785714285714366, -2.3857142857142932, -1.585714285714293, -1.29285714285715, -1.0571428571428643, -0.25714285714286433, -0.12857142857143572, -0.1285714285714357, -0.10714285714286424, -0.08571428571429283, -0.09285714285714998, 0.1428571428571357, 0.4142857142857071, 1.3428571428571359, 1.6928571428571357, 1.464285714285707, 1.1357142857142786, 0.9428571428571357, 1.4214285714285642, 1.5499999999999925, 1.9857142857142784, 2.2142857142857073, 2.9357142857142784, 3.849999999999992, 4.442857142857135, 4.771428571428563, 4.964285714285706, 5.057142857142849, 5.235714285714278, 5.614285714285706, 6.114285714285706, 6.678571428571421, 7.371428571428564, 7.549999999999992, 7.3499999999999925, 7.428571428571422, 7.2285714285714215, 7.085714285714279, 7.085714285714279, 7.057142857142851, 7.085714285714279, 7.142857142857137, 7.685714285714281, 8.357142857142852, 8.842857142857138, 9.207142857142854, 9.21428571428571, 9.392857142857139, 9.84285714285714, 10.364285714285712, 10.685714285714283, 10.828571428571426, 10.885714285714283, 10.378571428571425, 9.642857142857139, 8.764285714285709, 8.421428571428567, 8.21428571428571, 7.778571428571424, 7.449999999999996, 7.299999999999996, 7.449999999999996, 7.628571428571425, 7.578571428571424, 7.535714285714282, 7.828571428571424, 7.822380952380953, 7.963571428571429, 8.12904761904762, 8.328571428571431, 8.51714285714286, 8.651666666666669, 8.899285714285716, 9.071904761904765, 9.400476190476194, 9.740952380952384, 9.971904761904767, 10.289761904761908, 10.588809523809529, 10.718571428571433, 11.034047619047625, 11.169047619047626, 11.145238095238101, 11.245238095238102, 11.395238095238101, 11.521428571428578, 11.607142857142863, 11.744047619047624, 11.917857142857148, 12.099285714285719, 12.285000000000005, 12.335000000000006, 12.543333333333338, 12.856666666666673, 13.250238095238101, 13.785952380952386, 14.482380952380959, 15.2252380952381, 15.918095238095242, 16.495476190476193, 16.99428571428572, 17.363333333333337, 17.422857142857147, 17.58666666666667, 17.79738095238096, 18.048571428571435, 18.223571428571436, 18.416190476190483, 18.391666666666673, 18.22380952380953, 18.050000000000008, 17.950000000000006, 17.86071428571429, 17.895238095238096, 17.786904761904765, 17.70833333333334, 17.778571428571432, 17.889285714285716, 18.127380952380953, 18.417857142857144, 18.83452380952381, 19.14166666666667, 19.441666666666666, 19.71904761904762, 19.96547619047619, 20.045238095238094, 20.098809523809525, 20.080714285714286, 20.289047619047615, 20.50333333333333, 20.72595238095238, 21.030714285714282, 21.160476190476192, 21.218809523809522, 21.216428571428573, 21.29380952380953, 21.455714285714294, 21.733095238095245, 21.964047619047626, 22.183095238095245, 22.335476190476196, 22.577380952380963, 22.734523809523818, 22.895238095238106, 23.087857142857153, 23.11000000000001, 23.128571428571437, 23.103571428571435, 23.005476190476198, 23.02571428571429, 23.072142857142865, 23.053095238095246, 23.001904761904772, 23.0054761904762, 23.031666666666677, 23.047142857142866, 23.0054761904762, 23.038809523809537, 23.053333333333345, 23.213333333333345, 23.320952380952395, 23.461428571428588, 23.61309523809525, 23.62261904761906, 23.59523809523811, 23.532142857142873, 23.515476190476203, 23.469047619047636, 23.447619047619064, 23.340476190476206, 23.26190476190478, 23.12976190476192, 23.076190476190494, 22.887619047619065, 22.818571428571442, 22.725238095238108, 22.684761904761924, 22.726428571428592, 22.683571428571447, 22.650238095238112, 22.651904761904778, 22.653095238095254, 22.665000000000017, 22.712619047619064, 22.793571428571447, 22.71785714285716, 22.597619047619066, 22.5159523809524, 22.380238095238116, 22.255714285714305, 22.098571428571443, 22.020000000000014, 21.909285714285726, 21.729523809523823, 21.517142857142876, 21.329047619047635, 21.24928571428573, 21.199285714285732, 21.05642857142859, 21.06785714285716, 21.032142857142876, 21.044047619047635, 20.898809523809543, 20.67142857142859, 20.453571428571447, 20.135714285714304, 19.82142857142859, 19.721428571428593, 19.636904761904784, 19.529761904761926, 19.43690476190478, 19.316666666666688, 19.2309523809524, 19.042857142857162, 18.85952380952383, 18.736904761904782, 18.712142857142876, 18.843095238095255, 18.90500000000002, 18.985952380952398, 19.100238095238115, 19.033571428571445, 18.960952380952396, 18.676428571428584, 18.22404761904763, 17.785952380952395, 17.313333333333347, 16.9407142857143, 16.647857142857156, 16.189523809523823, 15.984523809523822, 15.775000000000011, 15.42261904761906, 15.061904761904772, 14.79761904761906, 14.45714285714287, 14.120238095238108, 13.988095238095251, 13.820238095238109, 13.704761904761918, 13.520238095238108, 13.264285714285725, 12.985714285714298, 12.816666666666679, 12.552380952380966, 12.159523809523822, 11.954761904761918, 11.73214285714287, 11.321428571428584, 10.898809523809534, 10.423809523809535, 10.041904761904773, 9.834285714285725, 9.622380952380963, 9.29309523809525, 9.100238095238108, 8.95857142857144, 8.78357142857144, 8.51214285714287, 8.339523809523822, 8.330000000000014, 8.269285714285727, 8.211428571428586, 8.1507142857143, 8.096428571428586, 7.917619047619061, 7.615714285714298, 7.222857142857156, 7.043809523809536, 6.822380952380965, 6.6200000000000125, 6.298571428571441, 5.896190476190489, 5.68309523809525, 5.3176190476190595, 4.894285714285725, 4.482857142857154, 4.0292857142857255, 3.6704761904762018, 3.5573809523809636, 3.64904761904763, 3.8430952380952488, 4.029285714285725, 4.056666666666677, 3.969761904761915, 3.9340476190476297, 3.966190476190487, 3.8483333333333443, 3.651904761904773, 3.5669047619047727, 3.536190476190487, 3.574285714285725, 3.471904761904772, 3.2730952380952485, 3.0421428571428675, 2.6909523809523916, 2.3285714285714394, 2.1083333333333445, 1.857142857142868, 1.626190476190487, 1.2797619047619155, 0.7866666666666774, 0.4371428571428679, -0.003333333333322625, -0.2771428571428464, -0.3271428571428464, -0.20928571428570358, -0.09142857142856073, -0.1088095238095131]
