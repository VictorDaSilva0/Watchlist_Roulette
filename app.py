import dash
from dash import html, dcc, Input, Output, State
import pandas as pd
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import random
import os

# 1. DONNÉES
base_path = os.path.dirname(__file__)
csv_path = os.path.join(base_path, 'data', 'watchlist.csv')

try:
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    if 'Year' in df.columns:
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce').fillna(0).astype(int)
except FileNotFoundError:
    df = pd.DataFrame({'Name': ['CSV non trouvé'], 'Year': [2026], 'Letterboxd URI': ['#']})

# Simulation
for col in ['Genre', 'AvgRating', 'FriendsRating']:
    if col not in df.columns:
        if col == 'Genre': df[col] = [random.choice(['Horreur', 'Drame', 'Action', 'Sci-Fi']) for _ in range(len(df))]
        else: df[col] = [round(random.uniform(2.5, 4.8), 1) for _ in range(len(df))]

# 2. APP
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# 3. LAYOUT
app.layout = html.Div(id="theme-container", children=[
    dbc.Container([
        # Header
        dbc.Row([
            dbc.Col(html.H1("LETTERBOXD ROULETTE", className="text-center my-5", 
                            style={'color': 'var(--accent-color)', 'fontWeight': '800'}), width=10),
            dbc.Col(dbc.Button(DashIconify(icon="lucide:moon", id="theme-icon", width=25), 
                               id="theme-toggle", color="link", className="mt-5"), width=2, className="text-end")
        ], align="center"),

        # SECTION HAUT
        dbc.Row([
            # Filtres
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([DashIconify(icon="bx:filter-alt", width=20, style={'marginRight': '10px'}), "Filtres"], className="mb-4"),
                        
                        html.Div([
                            html.Label([DashIconify(icon="mdi:movie-filter"), " Catégorie :"], className="filter-label"),
                            dcc.Dropdown(id='genre-filter', options=[{'label': g, 'value': g} for g in sorted(df['Genre'].unique())], multi=True, className="mb-3"),
                        ]),

                        html.Div([
                            html.Label([DashIconify(icon="material-symbols:star"), " Note Générale min :"], className="filter-label"),
                            dcc.Slider(id='rating-slider', min=0, max=5, step=0.5, value=3, 
                                       marks={i: str(i) for i in range(6)}), # CSS gère la couleur maintenant
                        ], style={'marginBottom': '35px'}),

                        html.Div([
                            html.Label([DashIconify(icon="ri:group-fill"), " Note des Amis min :"], className="filter-label"),
                            dcc.Slider(id='friends-slider', min=0, max=5, step=0.5, value=0, 
                                       marks={i: str(i) for i in range(6)}),
                        ], style={'marginBottom': '45px'}),

                        dbc.Button([DashIconify(icon="mdi:dice-multiple", width=20, style={'marginRight': '10px'}), "LANCER LA ROULETTE"], 
                                   id='spin-button', color="warning", className="w-100 py-3 fw-bold")
                    ])
                ], className="filter-card shadow")
            ], lg=5, md=12),

            # Résultat
            dbc.Col([
                html.Div(id='roulette-result', style={'height': '100%'})
            ], lg=7, md=12)
        ], className="mb-5 align-items-stretch"),

        # SECTION BAS
        html.Hr(style={'borderColor': 'var(--border-color)', 'margin': '40px 0'}),
        dbc.Row([
            dbc.Col([
                html.H3("Ma Watchlist Filtrée", className="mb-4 text-center text-lg-start"),
                html.Div(id='poster-grid', style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '25px'})
            ], width=12)
        ])
    ], fluid=True, style={'maxWidth': '1300px'})
], **{"data-theme": "dark"})

# 4. CALLBACKS
@app.callback(
    [Output("theme-container", "data-theme"), Output("theme-icon", "icon")],
    Input("theme-toggle", "n_clicks"),
    State("theme-container", "data-theme"),
    prevent_initial_call=True
)
def switch_theme(n, current):
    if current == "dark": return "light", "lucide:sun"
    return "dark", "lucide:moon"

@app.callback(
    [Output('roulette-result', 'children'), Output('poster-grid', 'children')],
    [Input('spin-button', 'n_clicks'), Input('genre-filter', 'value'),
     Input('rating-slider', 'value'), Input('friends-slider', 'value')]
)
def update_app(n_clicks, genres, min_rate, min_friends):
    dff = df[(df['AvgRating'] >= min_rate) & (df['FriendsRating'] >= min_friends)]
    if genres: dff = dff[dff['Genre'].isin(genres)]

    gallery = [
        html.A(
            html.Div([
                html.Div(row['Name'], className="movie-placeholder d-flex align-items-center justify-content-center p-3 text-center", 
                         style={'width': '140px', 'height': '210px', 'fontSize': '0.85rem', 'fontWeight': '600'}),
                html.Div([
                    DashIconify(icon="material-symbols:star", color="#ff8000", width=14),
                    html.Span(f" {row['AvgRating']}", style={'fontSize': '0.8rem', 'fontWeight': 'bold', 'marginLeft': '4px', 'color': 'var(--text-color)'})
                ], className="mt-2 text-center")
            ], className="poster-item"),
            href=row['Letterboxd URI'], target="_blank", style={'textDecoration': 'none'}
        ) for _, row in dff.iterrows()
    ]

    result = html.Div(
        dbc.Alert("Ajustez les filtres et lancez la roulette !", color="info", className="h-100 d-flex align-items-center justify-content-center text-center"),
        style={'height': '100%'}
    )
    
    if n_clicks and not dff.empty:
        sel = dff.sample(n=1).iloc[0]
        year_display = int(sel['Year']) if sel['Year'] > 0 else "N/A"
        
        result = dbc.Card([
            dbc.CardBody([
                DashIconify(icon="mdi:movie-open-star", width=50, color="var(--accent-color)", className="mb-3"),
                html.H2(sel['Name'], className="mb-3", style={'fontWeight': '800', 'color': 'var(--accent-color)'}),
                html.P([
                    DashIconify(icon="ph:calendar-bold"), f" {year_display}  •  ",
                    DashIconify(icon="ph:film-slate-bold"), f" {sel['Genre']}  •  ",
                    DashIconify(icon="material-symbols:star"), f" {sel['AvgRating']}  •  ",
                    DashIconify(icon="ri:group-line"), f" {sel['FriendsRating']}"
                ], className="mb-4", style={'opacity': '0.8', 'color': 'var(--text-color)'}),
                dbc.Button("VOIR LA FICHE LETTERBOXD", href=sel['Letterboxd URI'], target="_blank", color="warning", className="px-5 fw-bold")
            ])
        ], className="result-card text-center result-animation shadow-lg")
    
    return result, gallery

if __name__ == '__main__':
    app.run(debug=True)