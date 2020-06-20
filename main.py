#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
"""
Suggest movies based on user's ratings.
"""

import csv
import sys
import os
import json
import math
from tmdb_helper import TMDbMovie

MOVIE = TMDbMovie()

CONFIG_PATH = "config.json"

# Use format to insert user id when calling.
IMDB_USER_RATINGS_LINK = "https://www.imdb.com/user/ur{}/ratings?ref_=nv_usr_rt_4"

# TMDb API key link
TMDB_API_KEY_LINK = "https://www.themoviedb.org/settings/api"

RATINGS_PATH = "ratings.csv"
RATINGS_ENCRYPTION = "iso-8859-1"
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
                score = float(row[1])
                res[title] = score
    return res


def similar_movies(movie_id):
    """
    Finds similar movies of top result of search.
    """
    res = MOVIE.get_recommendations(movie_id)
    if not res:
        return []
    return res


def update_suggestions(ratings, status=True):
    """
    Generates suggestions based on ratings and saves them locally.
    @status: print status boolean
    """
    seen = []
    suggs = {}
    ratings_count = len(ratings)
    i = 0
    for title, rating in ratings.items():
        # Print progress
        if status:
            text = "\r{}/{} processed".format(i, ratings_count)
            sys.stdout.flush()
            sys.stdout.write(text)
            i += 1

        movs = MOVIE.search(title)
        if movs:
            movie_id = movs[0]["id"]
            seen.append(movie_id)
            for sugg in similar_movies(movie_id):
                if sugg["title"] in suggs:
                    suggs[sugg["title"]][0].append(rating)
                else:
                    suggs[sugg["title"]] = ([rating], sugg)

    # Calculate movie scores
    # personalized suggestions
    res = {}
    res_p = {}
    for title, (scores, data) in suggs.items():
        if not data["id"] in seen:
            res_p[title] = math.atan(data["popularity"]) * (
                (sum(scores)) / 10) / len(scores), len(scores), data
            res[title] = math.atan(data["popularity"]) * (
                (sum(scores) + data["vote_average"]) / 10) / (len(scores) + 1), len(scores), data

    # Sort on score
    res = sorted(res.items(), key=lambda item: item[1][0])
    res_p = sorted(res_p.items(), key=lambda item: item[1][0])

    # Write result to file
    with open(SUGGESTIONS_PATH, "w") as file:
        #for title, (score, relations, data) in res:
        file.write(json.dumps(res))
    with open(SUGGESTIONS_PERSONALIZED_PATH, "w") as file_p:
        #for title, (score, relations, data) in res:
        file_p.write(json.dumps(res_p))

    print()
    return res, res_p

def is_subset(subs, s):
    """
    Subset on lists.
    """
    return len([x for x in subs if x in s]) == len(subs)

def preview_suggestions(suggs, item_count=100, genres=None):
    """
    Uses 'less' to preview dict of movie suggestions.
    """
    id_to_genre = MOVIE.get_genres()
    full_text = ""
    count = 0
    for title, (score, relations, data) in reversed(suggs):
        movie_genres = [id_to_genre[g].lower() for g in data["genre_ids"]]
        if count == item_count:
            break
        if not genres or is_subset(genres, movie_genres):
            count += 1
            movie_item = "\e[33m{}\e[0m ({}) (match {:.2f}, relevance {})\n\tGenres: {}\n\tPopularity: {}\n\tRating: {}\n\t{}\n".format(
                title, data["release_date"].split("-")[0], score, relations,
                movie_genres, data["popularity"], data["vote_average"],
                "https://www.themoviedb.org/movie/" + str(data["id"]))
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

def movie_loop():
    """
    Loop options for movies.
    """
    user_input = ""

    while True:
        # clear terminal
        os.system('clear')

        # Print options
        print("Options:")
        print("\t's[uggest]' \t- preview {}".format(SUGGESTIONS_PATH))
        print("\t's[uggest] p[ersonalized]' \t- preview {}".format(SUGGESTIONS_PERSONALIZED_PATH))
        print("\t'g[enre]' \t- show genre options")
        print("\t'<genre>, ...' \t- preview {} filtered by genre".format(SUGGESTIONS_PATH))
        print("\t'u[pdate]' \t- update ratings.csv from imdb and generate suggestion files")

        # Option suggest (preview options with vim bindings)
        if command_match(user_input, "suggest"):
            preview_suggestions(_suggestions)
        # Option suggest personal (preview options with vim bindings)
        elif command_match(user_input, "suggest personalized"):
            preview_suggestions(_suggestions_p)

        # Option genre (print possible genres)
        elif command_match(user_input, "genre"):
            print("Genres:")
            for g_id, g in MOVIE.get_genres().items():
                print("\t{} - {}".format(g, g_id))

        # TODO Option <genre>, filter suggestions by <genre> and preview
        elif user_input and is_subset([x.strip() for x in user_input.split(",")], [g.lower() for g in MOVIE.get_genres().values()]):
            preview_suggestions(_suggestions, genres=[x.strip() for x in user_input.split(",")])

        # Option update ratings.csv from imdb and update suggestions.txt
        elif command_match(user_input, "update"):
            # TODO re-download ratings from imdb
            update_suggestions(_ratings)

        elif user_input == 'q':
            sys.exit(0)

        elif user_input:
            print("Command '{}' didn't match.".format(user_input))

        # Read user input
        user_input = input("Enter command: ")

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

    # Check for existing ratings
    if not os.path.exists(RATINGS_PATH):
        print("You have no ratings in this folder, either download manually or continue script")
        _ratings = download_imdb_ratings()
    else:
        _ratings = load_ratings()

    # Check for existing suggestions
    if os.path.exists(SUGGESTIONS_PATH) and os.path.exists(SUGGESTIONS_PERSONALIZED_PATH):
        with open(SUGGESTIONS_PATH, 'r') as _suggs:
            _suggestions = json.loads(_suggs.read())
        with open(SUGGESTIONS_PERSONALIZED_PATH, 'r') as _suggs:
            _suggestions_p = json.loads(_suggs.read())
    # Generate suggestion files
    else:
        update_suggestions(load_ratings())

    movie_loop()
