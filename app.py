import dash
from dash import html, dcc, Input, Output, State, callback_context, ALL
import pandas as pd
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import os
import json

# 1. PRÉPARATION DES DONNÉES
base_path = os.path.dirname(__file__)
enriched_path = os.path.join(base_path, 'data', 'watchlist_enriched.csv')

def load_data():
    if os.path.exists(enriched_path):
        data = pd.read_csv(enriched_path)
        if 'Watched' not in data.columns:
            data['Watched'] = False
        return data
    return pd.DataFrame(columns=['TitleFR', 'TitleInt', 'Year', 'Letterboxd URI', 'PosterURL', 'AvgRating', 'Genre', 'Watched'])

df = load_data()
df.columns = [c.strip() for c in df.columns]

# 2. FONCTIONS UTILITAIRES
def create_poster_card(row):
    img_src = row['PosterURL'] if row['PosterURL'] and str(row['PosterURL']) != 'nan' else ""
    
    # On détermine si le film est déjà vu pour le style
    is_watched = row['Watched']
    watched_class = "is-watched" if is_watched else ""
    
    return html.Div([
        # Bouton "Vu" - On le cache si le film est déjà marqué comme vu
        html.Button(
            DashIconify(icon="akar-icons:check", width=18, color="white"),
            id={'type': 'watch-button-list', 'index': row['Letterboxd URI']},
            className="btn-mark-watched-list",
            title="Marquer comme vu",
            style={'display': 'none'} if is_watched else {'zIndex': '999'}
        ),
        # Lien et Image
        html.A(
            html.Div([
                html.Img(src=img_src, className="movie-poster", 
                         style={'width': '140px', 'height': '210px', 'borderRadius': '10px', 'objectFit': 'cover'}),
                html.Div([
                    html.Div(row['TitleFR'], style={
                        'fontSize': '0.85rem', 'fontWeight': '600', 'marginTop': '8px', 
                        'whiteSpace': 'nowrap', 'overflow': 'hidden', 'textOverflow': 'ellipsis'
                    }),
                    html.Div([
                        DashIconify(icon="material-symbols:star", color="#ff8000", width=14),
                        html.Span(f" {row['AvgRating']}", style={'fontSize': '0.75rem', 'fontWeight': 'bold'})
                    ])
                ], className="text-center", style={'maxWidth': '140px'})
            ], className="poster-item"),
            href=row['Letterboxd URI'], target="_blank", style={'textDecoration': 'none', 'color': 'inherit'}
        )
    ], className=f"poster-container {watched_class}", style={'position': 'relative', 'display': 'inline-block'})

def clean_genre_name(name):
    return str(name).lower().replace(" ", "-").replace("é", "e").replace("ë", "e")

# 3. CONFIGURATION DE L'APP
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], update_title=None)
app.title = "Letterboxd Roulette"

# 4. LAYOUT
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
                            dcc.Dropdown(
                                id='genre-filter', 
                                options=[{'label': g, 'value': g} for g in sorted(df['Genre'].unique()) if str(g) != 'nan'], 
                                multi=True, className="mb-4"
                            ),
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
        
        # BARRE DE NAVIGATION
        dbc.Row([
            dbc.Col([
                html.H3("Ma Watchlist", className="mb-1"),
                html.P(id="movie-counter", style={'opacity': '0.6', 'fontSize': '0.9rem'})
            ], width=12, lg=4, className="text-center text-lg-start"),
            dbc.Col([
                dbc.Input(id="search-input", placeholder="Rechercher un film...", type="text")
            ], width=12, lg=4, className="my-3 my-lg-0"),
            dbc.Col([
                dcc.Dropdown(
                    id='sort-by',
                    options=[
                        {'label': 'Alphabétique', 'value': 'name_asc'},
                        {'label': 'Note (Plus haute)', 'value': 'rate_desc'},
                    ],
                    value='name_asc', clearable=False
                )
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
     Input('search-input', 'value'),
     Input({'type': 'watch-button-list', 'index': ALL}, 'n_clicks'),
     Input({'type': 'watch-button-roulette', 'index': ALL}, 'n_clicks')],
    [State('roulette-result', 'children')]
)
def update_app(n_spin, genres, min_rate, sort_val, search_val, n_list, n_roulette, current_res):
    global df
    ctx = callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # GESTION DU CLIC "VU"
    if triggered_id and 'watch-button' in triggered_id:
        trig_dict = json.loads(triggered_id)
        movie_uri = trig_dict['index']
        df.loc[df['Letterboxd URI'] == movie_uri, 'Watched'] = True
        df.to_csv(enriched_path, index=False)
        
        if 'watch-button-roulette' in trig_dict['type']:
            current_res = html.Div(dbc.Alert("Film archivé !", color="success", className="h-100 d-flex align-items-center justify-content-center"), style={'height': '100%'})

    # 1. FILTRAGE POUR LA ROULETTE (Seulement films non vus)
    roulette_pool = df[(df['AvgRating'] >= min_rate) & (df['Watched'] == False)].copy()
    if genres: roulette_pool = roulette_pool[roulette_pool['Genre'].isin(genres)]

    # 2. FILTRAGE POUR LA GRILLE
    dff = df.copy() 
    dff = dff[dff['AvgRating'] >= min_rate]
    if genres: dff = dff[dff['Genre'].isin(genres)]
    if search_val:
        dff = dff[dff['TitleFR'].str.contains(search_val, case=False, na=False)]

    # 3. LOGIQUE ROULETTE
    result_card = current_res
    if triggered_id == 'spin-button' and not roulette_pool.empty:
        sel = roulette_pool.sample(n=1).iloc[0]
        result_card = dbc.Card([
            dbc.CardBody([
                html.Img(src=sel['PosterURL'], style={'width': '180px', 'borderRadius': '10px', 'marginBottom': '20px'}),
                html.H2(sel['TitleFR'], style={'color': 'var(--accent-color)', 'fontWeight': '800'}),
                dbc.Button("VU ✅", id={'type': 'watch-button-roulette', 'index': sel['Letterboxd URI']}, color="success", className="fw-bold mt-2")
            ])
        ], className="result-card text-center shadow-lg")
    
    if result_card is None:
        result_card = html.Div(dbc.Alert("Lancez la roulette !", color="info", className="h-100 d-flex align-items-center justify-content-center"), style={'height': '100%'})

    # 4. TRI ET COMPTEUR
    if sort_val == 'name_asc': dff = dff.sort_values('TitleFR')
    elif sort_val == 'rate_desc': dff = dff.sort_values('AvgRating', ascending=False)

    remaining = len(df[df['Watched'] == False])
    count_text = f"{remaining} film(s) restants dans la liste"

    grid_content = html.Div([create_poster_card(row) for _, row in dff.iterrows()], className="d-flex flex-wrap gap-4 justify-content-center")

    return result_card, grid_content, count_text

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)