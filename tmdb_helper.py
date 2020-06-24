#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""

"""

import json
import requests

BASE_URL = "https://api.themoviedb.org/3"

class TMDb:
    api_key = ""

    def __init__(self, media_type):
        # movie or series
        self.media_type = media_type

    def __default_params(self):
        return {"api_key": self.api_key, "language": "en-US"}

    def search(self, movie_name):
        url = BASE_URL + "/search/{}".format(self.media_type)
        p = self.__default_params()
        p["query"] = movie_name
        res = requests.get(url, params=p)
        res = json.loads(res.text)
        return res["results"]

    def search_by_imdb_id(self, imdb_id):
        url = BASE_URL + "/find/{}".format(imdb_id)
        p = self.__default_params()
        p["external_source"] = "imdb_id"
        res = requests.get(url, params=p)
        res = json.loads(res.text)
        return res["{}_results".format(self.media_type)]

    def get_recommendations(self, media_id):
        """
        returns an array of movie recommendations based on query.
        """
        url = BASE_URL + "/{}/{}/recommendations"
        p = self.__default_params()
        res = requests.get(url.format(self.media_type, media_id), params=p)
        res = json.loads(res.text)
        return res['results']

    def get_genres(self):
        """
        Returns a dict of IDs -> names from TMDb
        """
        url = BASE_URL + "/genre/{}/list".format(self.media_type)
        p = self.__default_params()
        res = requests.get(url, params=p)
        res = json.loads(res.text)["genres"]
        res = {x["id"]: x["name"] for x in res}
        return res

def TMDbMovie():
    return TMDb("movie")
def TMDbTV():
    return TMDb("tv")
