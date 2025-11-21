#!/usr/bin/env python3

import csv
import os
import time
import csv
import requests
from datetime import datetime, timedelta

# ----------------- CONFIG -----------------
TMDB_API_KEY = os.getenv("TMDB_API_KEY") or ""  # set env var OR edit here (not recommended)
OUT_CSV = "movies_real.csv"
TARGET_COUNT = 1000       # change to 50 or 200 for a quick test
VOTE_COUNT_GTE = 1000       # increase to bias toward more "famous" films
BASE_SLEEP = 0.2         # seconds between requests
PAGE_SLEEP = 0.5           # seconds between discover pages
MAX_DISCOVER_PAGES = 1000  # safety cap
# ------------------------------------------

if not TMDB_API_KEY:
    raise SystemExit("Please set TMDB_API_KEY environment variable before running the script.")

SESSION = requests.Session()
API_BASE = "https://api.themoviedb.org/3"
DISCOVER_URL = API_BASE + "/discover/movie"
MOVIE_URL = API_BASE + "/movie/{movie_id}"
CREDITS_URL = API_BASE + "/movie/{movie_id}/credits"

def progress_bar(current, total, start_time, bar_length=40):
    fraction = current / total if total else 0
    filled = int(fraction * bar_length)
    bar = '█' * filled + '-' * (bar_length - filled)
    percent = fraction * 100
    elapsed = time.perf_counter() - start_time
    eta = (elapsed / current) * (total - current) if current and total else 0
    eta_str = str(timedelta(seconds=int(eta))) if eta else "00:00:00"
    print(f"\rProgress: |{bar}| {percent:6.2f}% ({current}/{total}) ETA: {eta_str}", end="", flush=True)

def discover_movies(page):
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "sort_by": "popularity.desc",
        "include_adult": "false",
        "include_video": "false",
        "page": page,
        "with_original_language": "en",
        "primary_release_date.gte": "2000-01-01",
        "vote_count.gte": VOTE_COUNT_GTE
    }
    resp = SESSION.get(DISCOVER_URL, params=params)
    resp.raise_for_status()
    return resp.json()

def get_movie_details(movie_id):
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    resp = SESSION.get(MOVIE_URL.format(movie_id=movie_id), params=params)
    resp.raise_for_status()
    return resp.json()

def get_movie_credits(movie_id):
    params = {"api_key": TMDB_API_KEY}
    resp = SESSION.get(CREDITS_URL.format(movie_id=movie_id), params=params)
    resp.raise_for_status()
    return resp.json()

def safe_text(s):
    if s is None:
        return ""
    return " ".join(str(s).split())

def extract_row(movie_detail, credits, assigned_id):
    title = safe_text(movie_detail.get("title") or movie_detail.get("original_title") or "")
    release_date = movie_detail.get("release_date") or ""
    year = release_date.split("-")[0] if release_date else ""
    description = safe_text(movie_detail.get("overview") or "")
    runtime = movie_detail.get("runtime") or ""
    rating = movie_detail.get("vote_average") or ""

    # director from crew
    director = ""
    for person in credits.get("crew", []):
        if person.get("job") == "Director":
            director = safe_text(person.get("name"))
            break

    # cast - top 5 by 'order'
    cast = sorted(credits.get("cast", []), key=lambda c: c.get("order", 999))
    top_cast = [safe_text(c.get("name")) for c in cast[:5]]
    while len(top_cast) < 5:
        top_cast.append("")

    genres = ", ".join([g.get("name") for g in movie_detail.get("genres", [])]) or ""

    return {
        "id": assigned_id,
        "title": title,
        "year": year,
        "description": description,
        "runtime": runtime,
        "rating": rating,
        "director": director,
        "actor1": top_cast[0],
        "actor2": top_cast[1],
        "actor3": top_cast[2],
        "actor4": top_cast[3],
        "actor5": top_cast[4],
        "genres": genres
    }

def main():
    fieldnames = ["id","title","year","description","runtime","rating","director",
                  "actor1","actor2","actor3","actor4","actor5","genres"]
    written = 0
    next_assign_id = 1
    page = 1
    start_time = time.perf_counter()
    backoff_seconds = BASE_SLEEP

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        while written < TARGET_COUNT and page <= MAX_DISCOVER_PAGES:
            try:
                data = discover_movies(page)
            except requests.HTTPError as e:
                # handle rate limit (429) with backoff and continue
                status = getattr(e.response, "status_code", None)
                print(f"\nDiscover page {page} error: {e} (status {status}). Backing off {backoff_seconds}s.")
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 10)
                continue

            results = data.get("results", [])
            if not results:
                print("\nNo more discover results; stopping.")
                break

            for item in results:
                if written >= TARGET_COUNT:
                    break

                movie_id = item.get("id")
                # fetch details + credits with naive retry/backoff
                try:
                    detail = get_movie_details(movie_id)
                    credits = get_movie_credits(movie_id)
                    backoff_seconds = BASE_SLEEP  # reset backoff on success
                except requests.HTTPError as e:
                    status = getattr(e.response, "status_code", None)
                    print(f"\nSkipping movie {movie_id} due to error: {e} (status {status}). Backing off {backoff_seconds}s.")
                    time.sleep(backoff_seconds)
                    backoff_seconds = min(backoff_seconds * 2, 10)
                    continue
                except Exception as e:
                    print(f"\nUnexpected error for movie {movie_id}: {e}. Skipping.")
                    time.sleep(BASE_SLEEP)
                    continue

                # sanity filters
                if detail.get("original_language") != "en":
                    time.sleep(BASE_SLEEP)
                    continue
                rd = detail.get("release_date") or ""
                if rd and rd < "2000-01-01":
                    time.sleep(BASE_SLEEP)
                    continue

                row = extract_row(detail, credits, next_assign_id)
                writer.writerow(row)
                written += 1
                next_assign_id += 1

                # progress display
                progress_bar(written, TARGET_COUNT, start_time)

                # polite pause
                time.sleep(BASE_SLEEP)

            page += 1
            time.sleep(PAGE_SLEEP)

    # finish line for progress
    print()  # newline
    elapsed_total = time.perf_counter() - start_time
    print(f"Finished. Wrote {written} movies to {OUT_CSV} in {timedelta(seconds=int(elapsed_total))}.")

if __name__ == "__main__":
    main()
