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

# Mapping des genres (identique au précédent)
GENRE_MAP = {
    28: "Action", 12: "Aventure", 16: "Animation", 35: "Comédie", 80: "Crime",
    99: "Documentaire", 18: "Drame", 10751: "Famille", 14: "Fantastique",
    36: "Histoire", 27: "Horreur", 10402: "Musique", 9648: "Mystère",
    10749: "Romance", 878: "Science-Fiction", 10770: "Téléfilm",
    53: "Thriller", 10752: "Guerre", 37: "Western"
}

def get_movie_details(title):
    if not API_KEY:
        print("Erreur : Clé API manquante dans le fichier .env")
        return None
        
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={title}&language=fr-FR"
    try:
        res = requests.get(search_url).json()
        if res.get('results'):
            movie = res['results'][0]
            genre_id = movie['genre_ids'][0] if movie['genre_ids'] else None
            genre_name = GENRE_MAP.get(genre_id, "Inconnu")
            
            return {
                'PosterURL': f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie['poster_path'] else None,
                'AvgRating': round(movie['vote_average'] / 2, 1),
                'Genre': genre_name
            }
    except Exception as e:
        print(f"Erreur pour {title}: {e}")
    return None

# --- Script principal ---
if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
        
    df = pd.read_csv(CSV_INPUT)
    df.columns = [c.strip() for c in df.columns]

    print(f"Enrichissement de {len(df)} films avec la clé du .env... 🍿")
    posters, ratings, genres = [], [], []

    for index, row in df.iterrows():
        print(f"[{index+1}/{len(df)}] Recherche : {row['Name']}")
        details = get_movie_details(row['Name'])
        
        if details:
            posters.append(details['PosterURL'])
            ratings.append(details['AvgRating'])
            genres.append(details['Genre'])
        else:
            posters.append(None)
            ratings.append(0.0)
            genres.append("Inconnu")
        
        time.sleep(0.1)

    df['PosterURL'] = posters
    df['AvgRating'] = ratings
    df['Genre'] = genres

    df.to_csv(CSV_OUTPUT, index=False)
    print(f"\n✅ Terminé ! Fichier créé : {CSV_OUTPUT}")