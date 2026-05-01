import dash
from dash import html, dcc, Input, Output, State, callback_context
import pandas as pd
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import os

# 1. PRÉPARATION DES DONNÉES
base_path = os.path.dirname(__file__)
enriched_path = os.path.join(base_path, 'data', 'watchlist_enriched.csv')

if os.path.exists(enriched_path):
    df = pd.read_csv(enriched_path)
else:
    df = pd.DataFrame({
        'TitleFR': ['Lancer enrich_data.py'], 
        'TitleInt': [''], 
        'Year': [0], 
        'Letterboxd URI': ['#'], 
        'PosterURL': [''], 
        'AvgRating': [0.0], 
        'Genre': ['Inconnu']
    })

df.columns = [c.strip() for c in df.columns]

# 2. FONCTIONS UTILITAIRES
def create_poster_card(row):
    img_src = row['PosterURL'] if row['PosterURL'] and str(row['PosterURL']) != 'nan' else ""
    return html.A(
        html.Div([
            html.Img(src=img_src, className="movie-poster", 
                     style={'width': '140px', 'height': '210px', 'borderRadius': '10px', 'objectFit': 'cover'}) if img_src else html.Div(row['TitleFR'], className="movie-placeholder"),
            html.Div([
                html.Div(row['TitleFR'], style={'fontSize': '0.85rem', 'fontWeight': '600', 'marginTop': '8px'}),
                html.Div([
                    DashIconify(icon="material-symbols:star", color="#ff8000", width=14),
                    html.Span(f" {row['AvgRating']}", style={'fontSize': '0.75rem', 'fontWeight': 'bold'})
                ])
            ], className="text-center", style={'maxWidth': '140px'})
        ], className="poster-item"),
        href=row['Letterboxd URI'], target="_blank", style={'textDecoration': 'none', 'color': 'inherit'}
    )

def clean_genre_name(name):
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
        
        # NAVIGATION
        dbc.Row([
            dbc.Col([
                html.H3("Ma Watchlist", className="mb-1"),
                html.P(id="movie-counter", style={'opacity': '0.6', 'fontSize': '0.9rem'})
            ], width=12, lg=4, className="text-center text-lg-start"),
            dbc.Col([
                dbc.Input(id="search-input", placeholder="Recherche titre FR ou Original...", type="text", 
                          style={'borderRadius': '10px', 'backgroundColor': 'var(--card-bg)', 'color': 'var(--text-color)'})
            ], width=12, lg=4, className="my-3 my-lg-0"),
            dbc.Col([
                html.Div([
                    html.Span("Trier : ", style={'marginRight': '10px', 'opacity': '0.8'}),
                    dcc.Dropdown(
                        id='sort-by',
                        options=[
                            {'label': 'Alphabétique', 'value': 'name_asc'},
                            {'label': 'Note (Plus haute)', 'value': 'rate_desc'},
                            {'label': 'Grouper par Genre', 'value': 'group_genre'},
                        ],
                        value='name_asc', clearable=False, style={'width': '180px', 'color': '#333'}
                    )
                ], className="d-flex align-items-center justify-content-center justify-content-lg-end")
            ], width=12, lg=4)
        ], className="mb-4 align-items-end"),

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
    [Output('roulette-result', 'children'), 
     Output('poster-grid', 'children'), 
     Output('movie-counter', 'children')],
    [Input('spin-button', 'n_clicks'), 
     Input('genre-filter', 'value'),
     Input('rating-slider', 'value'), 
     Input('sort-by', 'value'),
     Input('search-input', 'value')],
    [State('roulette-result', 'children')]
)
def update_app(n_clicks, genres, min_rate, sort_val, search_val, current_res):
    # Déterminer quel élément a déclenché le changement
    ctx = callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # 1. FILTRAGE GLOBAL
    dff = df[df['AvgRating'] >= min_rate].copy()
    if genres: dff = dff[dff['Genre'].isin(genres)]
    if search_val:
        dff = dff[dff['TitleFR'].str.contains(search_val, case=False, na=False) | 
                  dff['TitleInt'].str.contains(search_val, case=False, na=False)]

    # 2. GESTION DE LA ROULETTE
    # Par défaut, on garde le résultat actuel pour ne pas le réinitialiser en tapant
    result_card = current_res

    # Si c'est le bouton spin ou s'il n'y a pas encore de résultat
    if triggered_id == 'spin-button' and not dff.empty:
        sel = dff.sample(n=1).iloc[0]
        result_card = dbc.Card([
            dbc.CardBody([
                html.Img(src=sel['PosterURL'], style={'width': '180px', 'borderRadius': '10px', 'marginBottom': '20px', 'boxShadow': '0 10px 20px rgba(0,0,0,0.5)'}),
                html.H2(sel['TitleFR'], className="mb-1", style={'fontWeight': '800', 'color': 'var(--accent-color)'}),
                html.I(sel['TitleInt'], style={'display': 'block', 'marginBottom': '15px', 'color': '#ffffff', 'opacity': '0.8'}),
                html.P([
                    DashIconify(icon="ph:film-slate-bold"), f" {sel['Genre']}  •  ", 
                    DashIconify(icon="material-symbols:star"), f" {sel['AvgRating']}"
                ], style={'color': '#ffffff', 'fontWeight': '500'}),
                dbc.Button("FICHE LETTERBOXD", href=sel['Letterboxd URI'], target="_blank", color="warning", className="fw-bold mt-2")
            ])
        ], className="result-card text-center result-animation shadow-lg", key=f"res-{n_clicks}")
    
    # Message d'accueil si vide
    if result_card is None:
        result_card = html.Div(dbc.Alert("Lancez la roulette !", color="info", className="h-100 d-flex align-items-center justify-content-center"), style={'height': '100%'})

    # 3. GESTION DE LA GRILLE (Toujours mise à jour)
    if sort_val == 'name_asc': dff = dff.sort_values('TitleFR', ascending=True)
    elif sort_val == 'rate_desc': dff = dff.sort_values('AvgRating', ascending=False)

    count_text = f"{len(dff)} film(s) trouvé(s)"
    
    if sort_val == 'group_genre':
        grid_content = []
        for g_name in sorted(dff['Genre'].unique()):
            g_df = dff[dff['Genre'] == g_name]
            g_cls = clean_genre_name(g_name)
            grid_content.append(html.Div([
                html.Div([DashIconify(icon="mdi:movie-open", className=f"icon-{g_cls}", width=24), html.H4(g_name.upper(), className="genre-title")], className=f"genre-header genre-{g_cls} mt-5 mb-4"),
                html.Div([create_poster_card(row) for _, row in g_df.iterrows()], className="d-flex flex-wrap gap-4 justify-content-center")
            ]))
    else:
        grid_content = html.Div([create_poster_card(row) for _, row in dff.iterrows()], className="d-flex flex-wrap gap-4 justify-content-center")

    return result_card, grid_content, count_text

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)