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

about_page = html.Div([
    dbc.Row(dbc.Col(html.Div("About Us"))),
    dbc.Row(dbc.Col(html.Div("Our Team is scattered across North America, but is headquartered at the University of Waterloo. You can reach us at nafshordi@pitp.ca"))),
    dbc.Row(
        [
            dbc.Col([
              dbc.Row(html.Div("Niayesh Afshordi")),
              dbc.Row(html.Div("Associate Professor of Physics and Astronomy at the University of Waterloo and Associate Faculty in Cosmology at the Perimeter Institute for Theoretical Physics")),
            ]),
            dbc.Col([
              dbc.Row(html.Div("Mohammad Bahrami")),
              dbc.Row(html.Div("Wolfram Research")),
            ]),
            dbc.Col([
              dbc.Row(html.Div("Elizabeth Gould")),
              dbc.Row(html.Div("Postdoctoral Researcher at the Arthur B. McDonald Canadian Astroparticle Physics Research Institute")),
            ]),
            dbc.Col([
              dbc.Row(html.Div("Benjamin Holder")),
              dbc.Row(html.Div("Associate Professor of Physics at Grand Valley State University")),
            ]),
        ]
    ),
    dbc.Row(
        [
            dbc.Col([
              dbc.Row(html.Div("Shafika Olalekan Koiki")),
              dbc.Row(html.Div("Undergraduate Student in Physics and Astronomy at the University of Waterloo")),
            ]),
            dbc.Col([
              dbc.Row(html.Div("Daniel Lichblau")),
              dbc.Row(html.Div("Wolfram Research")),
            ]),
            dbc.Col([
              dbc.Row(html.Div("Steve Weinstein")),
              dbc.Row(html.Div("Associate Professor of Philosophy at the University of Waterloo")),
            ]),
            dbc.Col([
              dbc.Row(html.Div("Jolene Zheng")),
              dbc.Row(html.Div("Undergraduate Student in Computer Science at the University of Waterloo")),
            ]),
        ]
    ),
])

faq_page = html.Div([
    dbc.Row(dbc.Col(html.Div("FAQ"))),
    dbc.Row(dbc.Col(html.Div("Text goes here!"))),
])
