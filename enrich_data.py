import os
import pandas as pd
import requests
import time
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")

CSV_INPUT = "data/watchlist.csv"
CSV_OUTPUT = "data/watchlist_enriched.csv"

# Mapping des IDs de genres TMDB vers noms français
GENRE_MAP = {
    28: "Action", 12: "Aventure", 16: "Animation", 35: "Comédie", 80: "Crime",
    99: "Documentaire", 18: "Drame", 10751: "Famille", 14: "Fantastique",
    36: "Histoire", 27: "Horreur", 10402: "Musique", 9648: "Mystère",
    10749: "Romance", 878: "Science-Fiction", 10770: "Téléfilm",
    53: "Thriller", 10752: "Guerre", 37: "Western"
}

def get_movie_details(title):
    if not API_KEY:
        print("❌ Erreur : Clé API manquante dans le fichier .env")
        return None
        
    query = title.strip()
    search_url = "https://api.themoviedb.org/3/search/movie"
    # On demande les résultats en Français
    params = {
        "api_key": API_KEY,
        "query": query,
        "language": "fr-FR"
    }
    
    try:
        response = requests.get(search_url, params=params)
        res = response.json()
        
        if res.get('results'):
            movie = res['results'][0]
            genre_id = movie['genre_ids'][0] if movie.get('genre_ids') else None
            
            return {
                'TitleFR': movie.get('title'),           # Titre français
                'TitleInt': movie.get('original_title'),  # Titre original
                'PosterURL': f"https://image.tmdb.org/t/p/w185{movie['poster_path']}" if movie.get('poster_path') else "",
                'AvgRating': round(movie.get('vote_average', 0) / 2, 1),
                'Genre': GENRE_MAP.get(genre_id, "Inconnu")
            }
        else:
            print(f"⚠️ Aucun résultat pour : '{query}'")
    except Exception as e:
        print(f"❌ Erreur API pour '{query}': {e}")
    return None

if __name__ == "__main__":
    if not os.path.exists(CSV_INPUT):
        print(f"❌ Fichier source {CSV_INPUT} introuvable.")
        exit()

    df = pd.read_csv(CSV_INPUT)
    df.columns = [c.strip() for c in df.columns]

    print(f"🚀 Enrichissement de {len(df)} films (Titres FR + INT)...")
    
    new_data = []

    for index, row in df.iterrows():
        name = str(row.get('Name', ''))
        print(f"[{index+1}/{len(df)}] Recherche : {name}")
        
        details = get_movie_details(name)
        
        # On garde les infos de base de Letterboxd et on fusionne avec TMDB
        movie_info = {
            'Date': row.get('Date'),
            'Name': name,
            'Year': row.get('Year'),
            'Letterboxd URI': row.get('Letterboxd URI'),
            'TitleFR': details['TitleFR'] if details else name,
            'TitleInt': details['TitleInt'] if details else name,
            'PosterURL': details['PosterURL'] if details else "",
            'AvgRating': details['AvgRating'] if details else 0.0,
            'Genre': details['Genre'] if details else "Inconnu"
        }
        new_data.append(movie_info)
        time.sleep(0.1) # Pour respecter les limites de l'API

    # Sauvegarde
    df_enriched = pd.DataFrame(new_data)
    if not os.path.exists("data"): os.makedirs("data")
    df_enriched.to_csv(CSV_OUTPUT, index=False)
    print(f"\n✅ Terminé ! Fichier créé : {CSV_OUTPUT}")