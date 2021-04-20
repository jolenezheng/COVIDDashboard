import dash_html_components as html
import dash_bootstrap_components as dbc

introduction_text = "This portal provides resources and tools that could help individuals and policy makers with a scientific, balanced, and evidence-based approach to manage and navigate the COVID-19 Pandemic. It provides historical information, important demographics, and resulting stochastic forecasting for local counties (US) or Health Units (Canada), for adjustable vaccination and face-mask usage and social mobility reduction strategies. The model is simultaneously calibrated against more than 2500 distinct epidemics (over 100,000 reproduction number measurements), over the course of the COVID-19 pandemic."

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

card_content = [
    dbc.CardHeader("Niayesh Afshordi"),
    dbc.CardBody(
        [
            html.P(
                "Associate Professor of Physics and Astronomy at the University of Waterloo and Associate Faculty in Cosmology at the Perimeter Institute for Theoretical Physics",
                className="card-text",
            ),
        ]
    ),
]

about_page = row = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(html.Div("About Us")),
            ],
            align="start",
        ),
        dbc.Row(
            [
                dbc.Col(html.Div("Our Team is scattered across North America, but is headquartered at the University of Waterloo. You can reach us at nafshordi@pitp.ca")),
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
                ], color="primary", inverse=True)),
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
                ], color="primary", inverse=True)),
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
                ], color="primary", inverse=True)),
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
                ], color="primary", inverse=True)),
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
                ], color="primary", inverse=True)),
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
                ], color="primary", inverse=True)),
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

faq_page = html.Div([
    dbc.Row(html.Div([
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
    ])),
    dbc.Row(html.Div([
      dbc.Button(
        "Open collapse",
        id="q2",
        className="mb-3",
        color="primary",
      ),
      dbc.Collapse(
        dbc.Card(dbc.CardBody("This content is hidden in the collapse")),
        id="a2",
      ),
    ])),
])

