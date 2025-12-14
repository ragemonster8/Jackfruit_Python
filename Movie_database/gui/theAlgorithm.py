import csv

# ==========================
# LOAD MOVIES
# ==========================
def load_movies(csv_path):
    movies = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["year"] = int(row["year"]) if row["year"].strip() else None
            row["runtime"] = int(row["runtime"]) if row["runtime"].strip() else None
            row["rating"] = float(row["rating"]) if row["rating"].strip() else 0.0

            genres_raw = (row.get("genres") or "").replace("|", ",")
            row["genres_list"] = [g.strip().lower() for g in genres_raw.split(",") if g.strip()]

            actor_cols = ["actor1", "actor2", "actor3", "actor4", "actor5"]
            row["actors_list"] = [(row.get(c) or "").lower() for c in actor_cols if row.get(c)]

            row["director_clean"] = (row.get("director") or "").lower()

            movies.append(row)
    return movies


# ==========================
# FIND MOVIE
# ==========================
def find_movie_by_title(movies, title):
    title = title.lower().strip()
    for m in movies:
        if m["title"].lower() == title:
            return m
    return None


# ==========================
# SIMILARITY
# ==========================
def similarity(movie, liked, avg_year):
    score = 0.0
    score += len(set(movie["genres_list"]) & set(liked["genres_list"])) * 4
    score += len(set(movie["actors_list"]) & set(liked["actors_list"])) * 3
    if movie["director_clean"] == liked["director_clean"] and movie["director_clean"]:
        score += 8
    if movie["year"] and avg_year:
        score += max(0, 10 - abs(movie["year"] - avg_year))
    return score


def total_score(movie, liked_movies):
    years = [m["year"] for m in liked_movies if m["year"]]
    avg_year = sum(years) / len(years) if years else None
    return sum(similarity(movie, lm, avg_year) for lm in liked_movies) + movie["rating"] * 0.5


# ==========================
# MAIN FUNCTION FOR GUI
# ==========================
def main(csv_path, liked_titles, top_n=4):
    movies = load_movies(csv_path)

    liked_movies = []
    for t in liked_titles:
        m = find_movie_by_title(movies, t)
        if m:
            liked_movies.append(m)

    if not liked_movies:
        return []

    scored = []
    for movie in movies:
        if any(movie["id"] == lm["id"] for lm in liked_movies):
            continue
        scored.append({
            "title": movie["title"],
            "score": total_score(movie, liked_movies)
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]

