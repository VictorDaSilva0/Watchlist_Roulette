import dash
from dash import html, dcc, Input, Output, State
import pandas as pd
import dash_bootstrap_components as dbc
import random
import os

# 1. PRÉPARATION DES DONNÉES
base_path = os.path.dirname(__file__)
csv_path = os.path.join(base_path, 'data', 'watchlist.csv')

try:
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
except FileNotFoundError:
    df = pd.DataFrame({
        'Name': ['Charger votre CSV', 'Dans le dossier data'],
        'Year': [2026, 2026],
        'Letterboxd URI': ['https://letterboxd.com'] * 2
    })

# Simulation colonnes si absentes
for col, val in [('Genre', ['Horreur', 'Drame', 'Action']), ('AvgRating', [4.0, 3.5, 4.5]), ('FriendsRating', [3.0, 4.0, 2.0])]:
    if col not in df.columns:
        df[col] = [random.choice(val) if isinstance(val, list) else val for _ in range(len(df))]
        if col != 'Genre': df[col] = [round(random.uniform(2.5, 4.8), 1) for _ in range(len(df))]

# 2. INITIALISATION
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP]) 

# 3. LAYOUT
app.layout = html.Div(id="theme-container", children=[
    dbc.Container([
        # Header
        dbc.Row([
            dbc.Col(html.H1("🎬 LETTERBOXD ROULETTE", className="text-center my-4", 
                            style={'color': 'var(--accent-color)', 'fontWeight': '800'}), width=10),
            dbc.Col(dbc.Button("🌙", id="theme-toggle", color="dark", className="mt-4"), width=2, className="text-end")
        ], align="center"),

        dbc.Row([
            # PANNEAU DES FILTRES
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Filtres", className="mb-4", style={'borderBottom': '1px solid var(--border-color)', 'paddingBottom': '10px'}),
                        
                        # Groupe Catégorie
                        html.Div([
                            html.Label("Catégorie :", className="filter-label"),
                            dcc.Dropdown(
                                id='genre-filter',
                                options=[{'label': g, 'value': g} for g in sorted(df['Genre'].unique())],
                                multi=True, className="custom-dropdown"
                            ),
                        ], className="filter-group"),

                        # Groupe Note Générale
                        html.Div([
                            html.Label("Note Générale minimum :", className="filter-label"),
                            dcc.Slider(id='rating-slider', min=0, max=5, step=0.5, value=3,
                                       marks={i: {'label': str(i), 'style': {'color': 'var(--text-color)'}} for i in range(6)}),
                        ], className="filter-group"),

                        # Groupe Note Amis
                        html.Div([
                            html.Label("Note des Amis minimum :", className="filter-label"),
                            dcc.Slider(id='friends-slider', min=0, max=5, step=0.5, value=0,
                                       marks={i: {'label': str(i), 'style': {'color': 'var(--text-color)'}} for i in range(6)}),
                        ], className="filter-group"),

                        # Bouton
                        dbc.Button("LANCER LA ROULETTE 🎲", id='spin-button', color="warning", className="w-100 mt-2")
                    ])
                ], className="filter-card")
            ], lg=4, md=12),

            # ZONE RÉSULTATS
            dbc.Col([
                html.Div(id='roulette-result', className="mb-4"),
                html.Hr(style={'borderColor': 'var(--border-color)', 'margin': '30px 0'}),
                html.H3("Ma Watchlist Filtrée", className="mb-4", style={'fontSize': '1.3rem', 'fontWeight': '600'}),
                html.Div(id='poster-grid', style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '20px'})
            ], lg=8, md=12)
        ])
    ], fluid=True)
], **{"data-theme": "dark"})

# 4. CALLBACKS
@app.callback(
    [Output("theme-container", "data-theme"), Output("theme-toggle", "children")],
    [Input("theme-toggle", "n_clicks")],
    [State("theme-container", "data-theme")],
    prevent_initial_call=True
)
def switch_theme(n, current):
    if current == "dark": return "light", "☀️"
    return "dark", "🌙"

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
                html.Div(row['Name'], className="movie-placeholder", style={'width': '140px', 'height': '200px'}),
                html.P(f"⭐ {row['AvgRating']}", className="text-center mt-2", style={'fontSize': '0.8rem', 'color': 'var(--text-color)', 'fontWeight': 'bold'})
            ], className="poster-item"),
            href=row['Letterboxd URI'], target="_blank"
        ) for _, row in dff.iterrows()
    ]

    result = html.P("Ajustez les filtres et lancez la roulette pour choisir votre film du soir !", 
                    className="text-center", style={'opacity': '0.6', 'marginTop': '20px'})
    
    if n_clicks and not dff.empty:
        sel = dff.sample(n=1).iloc[0]
        result = dbc.Card([
            dbc.CardBody([
                html.H2(sel['Name'], style={'color': 'var(--accent-color)', 'fontWeight': 'bold'}),
                html.P(f"{sel['Year']}  •  {sel['Genre']}  •  Public: {sel['AvgRating']}⭐  •  Amis: {sel['FriendsRating']}⭐"),
                dbc.Button("VOIR LA FICHE LETTERBOXD", href=sel['Letterboxd URI'], target="_blank", color="warning", className="mt-2")
            ])
        ], className="text-center shadow-lg", style={'border': '2px solid var(--accent-color)'})
    elif dff.empty:
        result = dbc.Alert("Aucun film ne correspond à vos critères !", color="danger", className="text-center")

    return result, gallery

if __name__ == '__main__':
    app.run(debug=True)