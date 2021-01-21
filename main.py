#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
"""
Suggest movies and shows based on user's ratings.
"""

import csv
import sys
import os
import json
import math
from tmdb_helper import TMDbMovie, TMDbTV

MOVIE = TMDbMovie()
TV = TMDbTV()
GENRES = {}

CONFIG_PATH = "config.json"

# Use format to insert user id when calling.
IMDB_USER_RATINGS_LINK = "https://www.imdb.com/user/ur{}/ratings?ref_=nv_usr_rt_4"

# TMDb API key link
TMDB_API_KEY_LINK = "https://www.themoviedb.org/settings/api"

RATINGS_PATH = "ratings.csv"
RATINGS_ENCRYPTION = "iso-8859-1"
SUGGESTIONS_FOLDER = "suggestions"
SUGGESTIONS_PATH = "suggestions.txt"
SUGGESTIONS_PERSONALIZED_PATH = "suggestions_p.txt"

# if windows
if os.name == 'nt':
    PREVIEW_COMMAND = "more"
else:
    PREVIEW_COMMAND = "less"

def download_imdb_ratings():
    """
    Log in to IMDb and download user ratings, save to @RATINGS_PATH.
    """
    print("Option not implemented")
    sys.exit(1)
    return {}

class imdbData:
    def __init__(self, data):
        self.imdb_id = data[0]
        self.user_rating = float(data[1])
        self.rate_date = data[2]
        self.title = data[3]
        self.imdb_link = data[4]
        # movie, tvSeries or tvMiniSeries
        self.type = "movie" if data[5] == "movie" else "tv"
        self.avg_rating = data[6]
        self.genres = data[9].split(", ")
        self.votes = data[10]
        self.release_date = data[11]
        self.director = data[12]

def load_ratings():
    """
    Read ratings from RATINGS_PATH
    """
    res = {}
    with open(RATINGS_PATH, newline='', encoding=RATINGS_ENCRYPTION) as csvfile:
        spamreader = csv.reader(csvfile)
        for i, row in enumerate(spamreader):
            if i:
                title = row[3]
                res[title] = imdbData(row)
    return res


def similar_search(tmdb_obj, media_id):
    """
    Finds similar movies of top result of search.
    """
    res = tmdb_obj.get_recommendations(media_id)
    if not res:
        return []
    return res

def suggest_score(popularity, vote_average, scores):
    """
    Function of which suggestion scores are made.
    Modify this for different results.
    """
    # Popularity is calculated by searches, favourites, votes, etc: https://developers.themoviedb.org/3/getting-started/popularity
    # Popularity can vary from 100 (a popular old movie) to 2000 (newly released hyped movie)
    popularity_score = math.atan(popularity)
    # Relevance score rewards movies with many similar movies (from your scores). Set to '1' to ignore relevance.
    relevance_score = math.atan(math.sqrt(len(scores)*10))
    # how vote average on TMDb should affect the score. This function uses a circular shape.
    vote_average_score = math.sqrt(1-(1-vote_average/10)**1)
    # how the scores of your similar ratings should be affecting suggestions
    similar_average_score = (sum(scores) / 10) / len(scores)

    personified_score = popularity_score * similar_average_score * relevance_score
    score = popularity_score * similar_average_score * relevance_score * vote_average_score
    return score, personified_score

def update_suggestions(ratings, tmdb_obj, status=True):
    """
    Generates suggestions based on ratings and saves them locally.
    @status: print status boolean
    """
    seen = []
    suggs = {}
    ratings_count = len(ratings)
    i = 0
    for title, data in ratings.items():
        # Print progress
        if status:
            text = "\r{}/{} processed".format(i, ratings_count)
            sys.stdout.flush()
            sys.stdout.write(text)
            i += 1

        movs = tmdb_obj.search_by_imdb_id(data.imdb_id) if data.type == tmdb_obj.media_type else None
        if movs:
            movie_id = movs[0]["id"]
            seen.append(movie_id)
            for sugg in similar_search(tmdb_obj, movie_id):
                # Different key if tv or movie
                title = sugg["title"] if "title" in sugg else sugg["name"]
                if title in suggs:
                    suggs[title][0].append(data.user_rating)
                else:
                    suggs[title] = ([data.user_rating], sugg)

    # Calculate movie scores
    # personalized suggestions
    res = {}
    res_p = {}
    for title, (scores, data) in suggs.items():
        if not data["id"] in seen:
            s, s_p = suggest_score(data["popularity"], data["vote_average"], scores)
            res_p[title] = s_p, len(scores), data
            res[title] = s, len(scores), data

    # Sort on score
    res = sorted(res.items(), key=lambda item: item[1][0])
    res_p = sorted(res_p.items(), key=lambda item: item[1][0])

    if not os.path.exists(SUGGESTIONS_FOLDER):
        os.makedirs(SUGGESTIONS_FOLDER)
    # Write result to file
    with open(SUGGESTIONS_FOLDER + "/" + tmdb_obj.media_type + "_" + SUGGESTIONS_PATH, "w") as file:
        #for title, (score, relations, data) in res:
        file.write(json.dumps(res))
    with open(SUGGESTIONS_FOLDER + "/" + tmdb_obj.media_type + "_" + SUGGESTIONS_PERSONALIZED_PATH, "w") as file_p:
        #for title, (score, relations, data) in res:
        file_p.write(json.dumps(res_p))

    print()
    return res, res_p

def is_subset(subs, s):
    """
    Subset on lists.
    """
    return len([x for x in subs if x in s]) == len(subs)

def preview_suggestions(suggs, media_type="movie", item_count=100, genres=None):
    """
    Uses 'less' to preview dict of movie suggestions.
    """
    genre_inclusions = [g for g in genres if g[0] != '-'] if genres else None
    genre_exclusions = [g[1:] for g in genres if g[0] == '-'] if genres else None
    full_text = ""
    count = 0
    for title, (score, relations, data) in reversed(suggs):
        media_genres = [GENRES[g].lower() for g in data["genre_ids"]]
        if count == item_count:
            break

        # If genre filtering is off, or suggestion matches filter inclusion and exclusion rules
        if not (genre_inclusions or genre_exclusions) or is_subset(genre_inclusions, media_genres) and not set(genre_exclusions).intersection(media_genres):
            date = data["release_date"] if "release_date" in data else data["first_air_date"]
            count += 1
            movie_item = "\e[33m{}\e[0m ({}) (match {:.2f}, relevance {})\n\tGenres: {}\n\tPopularity: {}\n\tRating: {}\n\t{}\n".format(
                title, date.split("-")[0], score, relations,
                media_genres, data["popularity"], data["vote_average"],
                "https://www.themoviedb.org/{}/".format(media_type) + str(data["id"]))
            full_text += movie_item

    # TODO switch to subprocess?
    os.system('echo -e "{}" | {}'.format(full_text, PREVIEW_COMMAND))


def command_match(text, command):
    """
    Checks if each word in @text is equal to the beginning of respective word in @command
    """
    text = text.split()
    command = command.split()
    if len(text) != len(command):
        return False
    for i, val in enumerate(text):
        if val != command[i][:len(val)]:
            return False
    return True

def suggestion_loop(_suggestions, _suggestions_tv, _suggestions_p, _suggestions_tv_p):
    """
    Loop options for movies.
    """
    user_input = ""

    print("Note: All queries default to movie results.")
    print("Note: Personalized suggestions doesn't include average rating when calculating suggestions.")
    first = True

    while True:
        # clear terminal, but not for first loop
        if first:
            first = False
        else:
            os.system('clear')

        # Print options
        print("Options:")
        print("\t's[uggest] [tv]' \t- preview <media_type>_{}".format(SUGGESTIONS_PATH))
        print("\t's[uggest] [tv] p[ersonalized]' \t- preview <media_type>_{}".format(SUGGESTIONS_PERSONALIZED_PATH))
        print("\t'g[enre]' \t- show genre options")
        print("\t'[tv] [-]<genre>, ...' \t- preview <media_type>_{} filtered by genre[s]".format(SUGGESTIONS_PATH))
        print("\t'u[pdate]' \t- update ratings.csv from imdb and generate suggestion files")

        # Option suggest (preview options with vim bindings)
        if command_match(user_input, "suggest"):
            preview_suggestions(_suggestions)
        elif command_match(user_input, "suggest tv"):
            preview_suggestions(_suggestions_tv, media_type="tv")
        # Option suggest personal (preview options with vim bindings)
        elif command_match(user_input, "suggest personalized"):
            preview_suggestions(_suggestions_p)
        elif command_match(user_input, "suggest tv personalized"):
            preview_suggestions(_suggestions_tv_p, media_type="tv")

        # Option genre (print possible genres)
        elif command_match(user_input, "genre"):
            print("Genres:")
            for g_id, g in GENRES.items():
                print("\t{} - {}".format(g, g_id))

        # TODO Option <genre>, filter suggestions by <genre> and preview
        # TODO filter by multiple genres
        elif user_input and is_subset([x.strip().strip('-') for x in user_input.split(",")], [g.lower() for g in GENRES.values()]):
            preview_suggestions(_suggestions, genres=[x.strip() for x in user_input.split(",")])
        elif user_input and len(user_input.split()) > 1 and command_match(user_input.split()[0], "tv") and is_subset([x.strip().strip('-') for x in user_input.split(" ", 1)[1].split(",")], [g.lower() for g in GENRES.values()]):
            preview_suggestions(_suggestions_tv, media_type="tv", genres=[x.strip() for x in user_input.split(" ", 1)[1].split(",")])

        # Option update ratings.csv from imdb and update suggestions.txt
        elif command_match(user_input, "update"):
            # TODO download ratings directly from imdb
            _ratings = load_ratings()
            _suggestions, _suggestions_p = update_suggestions(_ratings, MOVIE)
            _suggestions_tv, _suggestions_tv_p = update_suggestions(_ratings, TV)

        elif user_input == 'q':
            sys.exit(0)

        elif user_input:
            print("Command '{}' didn't match.".format(user_input))

        # Read user input
        user_input = input("Enter command: ")

def local_suggestions_exists():
    return os.path.exists(SUGGESTIONS_FOLDER + "/" + "movie_" + SUGGESTIONS_PATH) and os.path.exists(SUGGESTIONS_FOLDER + "/" + "movie_" + SUGGESTIONS_PERSONALIZED_PATH) and os.path.exists(SUGGESTIONS_FOLDER + "/" + "tv_" + SUGGESTIONS_PATH) and os.path.exists(SUGGESTIONS_FOLDER + "/" + "tv_" + SUGGESTIONS_PERSONALIZED_PATH)


if __name__ == "__main__":
    # Check config.json for validation (tmdb api)
    if not os.path.exists(CONFIG_PATH):
        print("No config exists, running initial setup")
        api_key = input("Enter TMDb API key ({}):".format(TMDB_API_KEY_LINK))
        conf = {"api_key": api_key}
        with open(CONFIG_PATH, 'w') as file:
            file.write(json.dumps(conf))
    # Read API key from config
    with open(CONFIG_PATH, 'r') as file:
        conf = json.loads(file.read())
    MOVIE.api_key = conf["api_key"]

    TV.api_key = conf["api_key"]
    GENRES.update(MOVIE.get_genres())
    GENRES.update(TV.get_genres())

    # Check for existing ratings
    if not os.path.exists(RATINGS_PATH):
        print("You have no ratings in this folder, either download manually or continue script")
        _ratings = download_imdb_ratings()
    else:
        _ratings = load_ratings()

    # Check for existing suggestions
    if local_suggestions_exists():
        with open(SUGGESTIONS_FOLDER + "/" + "movie_" + SUGGESTIONS_PATH, 'r') as _suggs:
            _suggestions = json.loads(_suggs.read())
        with open(SUGGESTIONS_FOLDER + "/" + "movie_" + SUGGESTIONS_PERSONALIZED_PATH, 'r') as _suggs:
            _suggestions_p = json.loads(_suggs.read())
        with open(SUGGESTIONS_FOLDER + "/" + "tv_" + SUGGESTIONS_PATH, 'r') as _suggs:
            _suggestions_tv = json.loads(_suggs.read())
        with open(SUGGESTIONS_FOLDER + "/" + "tv_" + SUGGESTIONS_PERSONALIZED_PATH, 'r') as _suggs:
            _suggestions_tv_p = json.loads(_suggs.read())
    # Generate suggestion files
    else:
        _suggestions, _suggestions_p = update_suggestions(_ratings, MOVIE)
        _suggestions_tv, _suggestions_tv_p = update_suggestions(_ratings, TV)

    suggestion_loop(_suggestions, _suggestions_tv, _suggestions_p, _suggestions_tv_p)
