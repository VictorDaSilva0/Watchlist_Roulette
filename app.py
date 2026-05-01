import dash
from dash import html, dcc, Input, Output, State
import pandas as pd
import dash_bootstrap_components as dbc
import random
import os

# 1. CONFIGURATION ET CHARGEMENT DES DONNÉES
# On cherche le fichier dans le dossier 'data'
base_path = os.path.dirname(__file__)
csv_path = os.path.join(base_path, 'data', 'watchlist.csv')

try:
    df = pd.read_csv(csv_path)
    # Nettoyage des noms de colonnes (parfois il y a des espaces dans l'export)
    df.columns = [c.strip() for c in df.columns]
except FileNotFoundError:
    # Création de données factices si le fichier n'existe pas encore pour tester l'interface
    data = {
        'Name': ['Inception', 'The Shining', 'Parasite', 'Mad Max'],
        'Year': [2010, 1980, 2019, 2015],
        'Letterboxd URI': ['https://letterboxd.com/film/inception/'] * 4
    }
    df = pd.DataFrame(data)

# --- SIMULATION DES DONNÉES MANQUANTES DANS LE CSV ---
# (Comme discuté, le CSV Letterboxd ne contient pas les genres/notes par défaut)
if 'Genre' not in df.columns:
    genres_possibles = ['Horreur', 'Drame', 'Action', 'Sci-Fi', 'Comédie', 'Thriller']
    df['Genre'] = [random.choice(genres_possibles) for _ in range(len(df))]

if 'AvgRating' not in df.columns:
    df['AvgRating'] = [round(random.uniform(2.5, 4.8), 1) for _ in range(len(df))]

if 'FriendsRating' not in df.columns:
    df['FriendsRating'] = [round(random.uniform(2.0, 5.0), 1) for _ in range(len(df))]

# 2. INITIALISATION DE L'APPLI (Thème Sombre)
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.CYBORG],
    title="Letterboxd Roulette"
)

# 3. LAYOUT (INTERFACE)
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col(html.H1("🎬 LETTERBOXD ROULETTE", className="text-center my-4", 
                        style={'color': '#ff8000', 'fontWeight': 'bold', 'letterSpacing': '2px'}), width=12)
    ]),

    dbc.Row([
        # PANNEAU DE CONTRÔLE (GAUCHE)
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Filtres", className="card-title mb-4"),
                    
                    html.Label("Catégorie :"),
                    dcc.Dropdown(
                        id='genre-filter',
                        options=[{'label': g, 'value': g} for g in sorted(df['Genre'].unique())],
                        multi=True,
                        placeholder="Tous les genres",
                        className="mb-4",
                        style={'color': '#000'}
                    ),
                    
                    html.Label("Note Moyenne Générale (Min) :"),
                    dcc.Slider(id='rating-slider', min=0, max=5, step=0.5, value=3,
                               marks={i: {'label': str(i), 'style': {'color': 'white'}} for i in range(6)},
                               className="mb-4"),
                    
                    html.Label("Note de mes Amis (Min) :"),
                    dcc.Slider(id='friends-rating-slider', min=0, max=5, step=0.5, value=0,
                               marks={i: {'label': str(i), 'style': {'color': 'white'}} for i in range(6)},
                               className="mb-4"),
                    
                    dbc.Button("LANCER LA ROULETTE 🎲", id='spin-button', color="warning", 
                               className="w-100 mt-2", style={'fontWeight': 'bold', 'fontSize': '1.2rem'}),
                ])
            ], style={'backgroundColor': '#2c3440', 'border': '1px solid #445566'})
        ], lg=4, md=12, className="mb-4"),

        # AFFICHAGE DES RÉSULTATS (DROITE)
        dbc.Col([
            # Zone du film tiré au sort
            html.Div(id='roulette-result', className="mb-5"),
            
            # Grille des films
            html.Hr(style={'color': '#445566'}),
            html.H3("Ma Watchlist Filtrée", className="mb-4", style={'fontSize': '1.4rem'}),
            html.Div(id='poster-grid', style={
                'display': 'flex', 
                'flexWrap': 'wrap', 
                'justifyContent': 'center',
                'gap': '15px'
            })
        ], lg=8, md=12)
    ])
], fluid=True, style={'padding': '20px'})

# 4. LOGIQUE (CALLBACK)
@app.callback(
    [Output('roulette-result', 'children'),
     Output('poster-grid', 'children')],
    [Input('spin-button', 'n_clicks'),
     Input('genre-filter', 'value'),
     Input('rating-slider', 'value'),
     Input('friends-rating-slider', 'value')]
)
def update_app(n_clicks, selected_genres, min_rating, min_friends_rating):
    # Filtrage du DataFrame
    dff = df[
        (df['AvgRating'] >= min_rating) & 
        (df['FriendsRating'] >= min_friends_rating)
    ]
    
    if selected_genres:
        dff = dff[dff['Genre'].isin(selected_genres)]

    # Création de la galerie de posters
    # Note: On utilise un placeholder coloré car le CSV n'a pas les images
    gallery = []
    for _, row in dff.iterrows():
        movie_card = html.A(
            html.Div([
                html.Div(row['Name'], style={
                    'width': '130px', 'height': '190px', 
                    'backgroundColor': '#445566', 'borderRadius': '8px',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                    'textAlign': 'center', 'padding': '10px', 'fontSize': '0.9rem',
                    'color': '#fff', 'border': '2px solid #556677'
                }),
                html.P(f"⭐ {row['AvgRating']}", className="text-center mt-1", style={'fontSize': '0.8rem'})
            ], className="poster-item"),
            href=row['Letterboxd URI'], target="_blank", style={'textDecoration': 'none'}
        )
        gallery.append(movie_card)

    # Logique du bouton roulette
    result = html.Div(
        dbc.Alert("Sélectionnez vos critères et lancez la roulette !", color="info"),
        className="text-center"
    )

    if n_clicks and n_clicks > 0:
        if not dff.empty:
            selection = dff.sample(n=1).iloc[0]
            result = dbc.Card([
                dbc.Row([
                    dbc.Col(
                        html.Div("🎬", style={'fontSize': '5rem', 'textAlign': 'center', 'padding': '20px'}),
                        width=4, className="d-flex align-items-center justify-content-center"
                    ),
                    dbc.Col(dbc.CardBody([
                        html.H2(selection['Name'], style={'color': '#ff8000'}),
                        html.H5(f"Année : {selection['Year']}"),
                        html.P(f"Genre : {selection['Genre']} | Public : {selection['AvgRating']}⭐ | Amis : {selection['FriendsRating']}⭐"),
                        dbc.Button("VOIR LA FICHE", href=selection['Letterboxd URI'], target="_blank", color="warning", size="sm")
                    ]), width=8)
                ])
            ], style={'backgroundColor': '#14181c', 'border': '2px solid #ff8000', 'borderRadius': '15px'})
        else:
            result = dbc.Alert("Aucun film ne correspond à ces critères dans votre watchlist !", color="danger")

    return result, gallery

# 5. EXECUTION
if __name__ == '__main__':
    app.run(debug=True)