import dash
from dash import html, dcc, Input, Output, State
import pandas as pd
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import random
import os

# 1. PRÉPARATION DES DONNÉES
base_path = os.path.dirname(__file__)
enriched_path = os.path.join(base_path, 'data', 'watchlist_enriched.csv')

if os.path.exists(enriched_path):
    df = pd.read_csv(enriched_path)
else:
    df = pd.DataFrame({'Name': ['Lancer enrich_data.py'], 'Year': [0], 'Letterboxd URI': ['#'], 'PosterURL': [''], 'AvgRating': [0.0], 'Genre': ['Inconnu']})

df.columns = [c.strip() for c in df.columns]
if 'Year' in df.columns:
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce').fillna(0).astype(int)

# 2. FONCTIONS UTILITAIRES
def create_poster_card(row):
    img_src = row['PosterURL'] if row['PosterURL'] and str(row['PosterURL']) != 'nan' else ""
    return html.A(
        html.Div([
            html.Img(src=img_src, className="movie-poster", 
                     style={'width': '140px', 'height': '210px', 'borderRadius': '10px', 'objectFit': 'cover'}) if img_src else html.Div(row['Name'], className="movie-placeholder"),
            html.Div([
                DashIconify(icon="material-symbols:star", color="#ff8000", width=14),
                html.Span(f" {row['AvgRating']}", style={'fontSize': '0.8rem', 'fontWeight': 'bold', 'color': 'var(--text-color)'})
            ], className="mt-2 text-center")
        ], className="poster-item"),
        href=row['Letterboxd URI'], target="_blank", style={'textDecoration': 'none'}
    )

def clean_genre_name(name):
    """Transforme 'Science-Fiction' en 'science-fiction' pour le CSS"""
    return str(name).lower().replace(" ", "-").replace("é", "e").replace("ë", "e")

# 3. CONFIGURATION DE L'APP
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Letterboxd Roulette"

# 4. INTERFACE (LAYOUT)
app.layout = html.Div(id="theme-container", children=[
    dbc.Container([
        # Header
        dbc.Row([
            dbc.Col(html.H1("LETTERBOXD ROULETTE", className="text-center my-5", 
                            style={'color': 'var(--accent-color)', 'fontWeight': '800'}), width=10),
            dbc.Col(dbc.Button(DashIconify(icon="lucide:moon", id="theme-icon", width=25), 
                               id="theme-toggle", color="link", className="mt-5"), width=2, className="text-end")
        ], align="center"),

        # SECTION ROULETTE
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([DashIconify(icon="bx:filter-alt", width=20, style={'marginRight': '10px'}), "Filtres"], className="mb-4"),
                        html.Div([
                            html.Label([DashIconify(icon="mdi:movie-filter"), " Catégorie :"], className="filter-label"),
                            dcc.Dropdown(id='genre-filter', options=[{'label': g, 'value': g} for g in sorted(df['Genre'].unique())], multi=True, className="mb-4"),
                        ]),
                        html.Div([
                            html.Label([DashIconify(icon="material-symbols:star"), " Note min :"], className="filter-label"),
                            dcc.Slider(id='rating-slider', min=0, max=5, step=0.5, value=3, marks={i: str(i) for i in range(6)}),
                        ], style={'marginBottom': '50px'}),
                        dbc.Button([DashIconify(icon="mdi:dice-multiple", width=20, style={'marginRight': '10px'}), "LANCER LA ROULETTE"], 
                                   id='spin-button', color="warning", className="w-100 py-3 fw-bold")
                    ])
                ], className="filter-card shadow")
            ], lg=5, md=12),
            dbc.Col([html.Div(id='roulette-result', style={'height': '100%'})], lg=7, md=12)
        ], className="mb-5 align-items-stretch"),

        html.Hr(style={'borderColor': 'var(--border-color)', 'margin': '40px 0'}),
        
        # SECTION TRI & GRILLE
        dbc.Row([
            dbc.Col(html.H3("Ma Watchlist", className="mb-4"), width=12, lg=6),
            dbc.Col([
                html.Div([
                    html.Span("Trier par : ", style={'marginRight': '10px', 'opacity': '0.8'}),
                    dcc.Dropdown(
                        id='sort-by',
                        options=[
                            {'label': 'Alphabétique (A-Z)', 'value': 'name_asc'},
                            {'label': 'Alphabétique (Z-A)', 'value': 'name_desc'},
                            {'label': 'Note (Plus haute)', 'value': 'rate_desc'},
                            {'label': 'Grouper par Genre', 'value': 'group_genre'},
                        ],
                        value='name_asc', clearable=False, style={'width': '220px', 'color': '#333'}
                    )
                ], className="d-flex align-items-center justify-content-lg-end mb-4")
            ], width=12, lg=6)
        ]),

        html.Div(id='poster-grid')
    ], fluid=True, style={'maxWidth': '1300px'})
], **{"data-theme": "dark"})

# 5. CALLBACKS
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
     Input('rating-slider', 'value'), Input('sort-by', 'value')]
)
def update_app(n_clicks, genres, min_rate, sort_val):
    dff = df[df['AvgRating'] >= min_rate].copy()
    if genres: dff = dff[dff['Genre'].isin(genres)]

    if sort_val == 'name_asc': dff = dff.sort_values('Name', ascending=True)
    elif sort_val == 'name_desc': dff = dff.sort_values('Name', ascending=False)
    elif sort_val == 'rate_desc': dff = dff.sort_values('AvgRating', ascending=False)

    # Roulette Result
    result = html.Div(dbc.Alert("Lancez la roulette !", color="info", className="h-100 d-flex align-items-center justify-content-center"), style={'height': '100%'})
    if n_clicks and not dff.empty:
        sel = dff.sample(n=1).iloc[0]
        result = dbc.Card([
            dbc.CardBody([
                html.Img(src=sel['PosterURL'], style={'width': '180px', 'borderRadius': '10px', 'marginBottom': '20px'}) if sel['PosterURL'] else "",
                html.H2(sel['Name'], className="mb-2", style={'fontWeight': '800', 'color': 'var(--accent-color)'}),
                html.P([DashIconify(icon="ph:film-slate-bold"), f" {sel['Genre']}  •  ", DashIconify(icon="material-symbols:star"), f" {sel['AvgRating']}"], style={'opacity': '0.8'}),
                dbc.Button("VOIR SUR LETTERBOXD", href=sel['Letterboxd URI'], target="_blank", color="warning", className="fw-bold")
            ])
        ], className="result-card text-center result-animation shadow-lg", key=f"res-{n_clicks}")

    # Grille de films
    if sort_val == 'group_genre':
        grid_content = []
        for g_name in sorted(dff['Genre'].unique()):
            g_df = dff[dff['Genre'] == g_name]
            g_cls = clean_genre_name(g_name)
            section = html.Div([
                html.Div([
                    DashIconify(icon="mdi:movie-open", className=f"icon-{g_cls}", width=24),
                    html.H4(g_name.upper(), className="genre-title")
                ], className=f"genre-header genre-{g_cls} mt-5 mb-4"),
                html.Div([create_poster_card(row) for _, row in g_df.iterrows()], className="d-flex flex-wrap gap-4 justify-content-center")
            ])
            grid_content.append(section)
    else:
        grid_content = html.Div([create_poster_card(row) for _, row in dff.iterrows()], className="d-flex flex-wrap gap-4 justify-content-center")

    return result, grid_content

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)