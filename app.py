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
    print("✅ Données enrichies chargées.")
else:
    # Fallback si le script d'enrichissement n'a pas été lancé
    df = pd.DataFrame({
        'Name': ['Lancer enrich_data.py svp'], 
        'Year': [0], 
        'Letterboxd URI': ['#'], 
        'PosterURL': [''], 
        'AvgRating': [0.0], 
        'Genre': ['Inconnu']
    })

df.columns = [c.strip() for c in df.columns]
if 'Year' in df.columns:
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce').fillna(0).astype(int)

# 2. CONFIGURATION DE L'APP
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Letterboxd Roulette"

# 3. INTERFACE (LAYOUT)
app.layout = html.Div(id="theme-container", children=[
    dbc.Container([
        # Header avec Toggle de thème
        dbc.Row([
            dbc.Col(html.H1("LETTERBOXD ROULETTE", className="text-center my-5", 
                            style={'color': 'var(--accent-color)', 'fontWeight': '800'}), width=10),
            dbc.Col(dbc.Button(DashIconify(icon="lucide:moon", id="theme-icon", width=25), 
                               id="theme-toggle", color="link", className="mt-5"), width=2, className="text-end")
        ], align="center"),

        # SECTION PRINCIPALE (Filtres + Résultat)
        dbc.Row([
            # Colonne Gauche : FILTRES
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([DashIconify(icon="bx:filter-alt", width=20, style={'marginRight': '10px'}), "Filtres"], className="mb-4"),
                        
                        html.Div([
                            html.Label([DashIconify(icon="mdi:movie-filter"), " Catégorie :"], className="filter-label"),
                            dcc.Dropdown(
                                id='genre-filter', 
                                options=[{'label': g, 'value': g} for g in sorted(df['Genre'].unique())], 
                                multi=True, className="mb-4"
                            ),
                        ]),

                        html.Div([
                            html.Label([DashIconify(icon="material-symbols:star"), " Note Générale min :"], className="filter-label"),
                            dcc.Slider(
                                id='rating-slider', min=0, max=5, step=0.5, value=3, 
                                marks={i: str(i) for i in range(6)}
                            ),
                        ], style={'marginBottom': '50px'}),

                        dbc.Button([DashIconify(icon="mdi:dice-multiple", width=20, style={'marginRight': '10px'}), "LANCER LA ROULETTE"], 
                                   id='spin-button', color="warning", className="w-100 py-3 fw-bold")
                    ])
                ], className="filter-card shadow")
            ], lg=5, md=12),

            # Colonne Droite : RÉSULTAT ROULETTE
            dbc.Col([
                html.Div(id='roulette-result', style={'height': '100%'})
            ], lg=7, md=12)
        ], className="mb-5 align-items-stretch"),

        # SECTION BASSE (GALERIE)
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
     Input('rating-slider', 'value')]
)
def update_app(n_clicks, genres, min_rate):
    # Filtrage des données
    dff = df[df['AvgRating'] >= min_rate]
    if genres: 
        dff = dff[dff['Genre'].isin(genres)]

    # Construction de la galerie (limitée à 40 pour la performance réseau)
    dff_view = dff.head(40)
    gallery = []
    for _, row in dff_view.iterrows():
        img_content = html.Img(
            src=row['PosterURL'], 
            className="movie-poster", 
            style={'width': '140px', 'height': '210px', 'borderRadius': '10px', 'objectFit': 'cover'}
        ) if row['PosterURL'] and str(row['PosterURL']) != 'nan' else html.Div(row['Name'], className="movie-placeholder", style={'width': '140px', 'height': '210px'})
        
        gallery.append(html.A(
            html.Div([
                img_content,
                html.Div([
                    DashIconify(icon="material-symbols:star", color="#ff8000", width=14),
                    html.Span(f" {row['AvgRating']}", style={'fontSize': '0.8rem', 'fontWeight': 'bold', 'color': 'var(--text-color)'})
                ], className="mt-2 text-center")
            ], className="poster-item"),
            href=row['Letterboxd URI'], target="_blank", style={'textDecoration': 'none'}
        ))

    # Gestion du résultat de la roulette
    default_msg = html.Div(
        dbc.Alert("Ajustez vos critères et lancez les dés !", color="info", className="h-100 d-flex align-items-center justify-content-center text-center"),
        style={'height': '100%'}
    )
    
    if n_clicks and not dff.empty:
        sel = dff.sample(n=1).iloc[0]
        year_val = int(sel['Year']) if sel['Year'] > 0 else "N/A"
        
        poster_src = sel['PosterURL'] if sel['PosterURL'] and str(sel['PosterURL']) != 'nan' else ""
        
        # Le paramètre key=f"result-{n_clicks}" force le rechargement de l'animation CSS
        result_card = dbc.Card([
            dbc.CardBody([
                html.Img(src=poster_src, style={'width': '180px', 'borderRadius': '10px', 'marginBottom': '20px', 'boxShadow': '0 10px 20px rgba(0,0,0,0.5)'}) if poster_src else "",
                html.H2(sel['Name'], className="mb-2", style={'fontWeight': '800', 'color': 'var(--accent-color)'}),
                html.P([
                    DashIconify(icon="ph:calendar-bold"), f" {year_val}  •  ",
                    DashIconify(icon="ph:film-slate-bold"), f" {sel['Genre']}  •  ",
                    DashIconify(icon="material-symbols:star"), f" {sel['AvgRating']}"
                ], className="mb-4", style={'opacity': '0.8', 'color': 'var(--text-color)'}),
                dbc.Button("VOIR SUR LETTERBOXD", href=sel['Letterboxd URI'], target="_blank", color="warning", className="px-5 fw-bold")
            ])
        ], 
        className="result-card text-center result-animation shadow-lg",
        key=f"result-{n_clicks}" 
        )
        return result_card, gallery

    return default_msg, gallery

# 5. DÉMARRAGE
if __name__ == '__main__':
    # On reste sur 0.0.0.0 pour ton téléphone. 
    # debug=False pour améliorer la vitesse de chargement sur mobile.
    app.run(debug=False, host='0.0.0.0', port=8050)