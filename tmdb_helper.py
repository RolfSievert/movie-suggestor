#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""

"""

import json
import requests

BASE_URL = "https://api.themoviedb.org/3"

class TMDbMovie:
    api_key = ""

    def __default_params(self):
        return {"api_key": self.api_key, "language": "en-US"}

    def search(self, movie_name):
        url = BASE_URL + "/search/movie"
        p = self.__default_params()
        p["query"] = movie_name
        res = requests.get(url, params=p)
        res = json.loads(res.text)
        return res["results"]

    def get_recommendations(self, movie_id):
        """
        returns an array of movie recommendations based on query.
        """
        url = BASE_URL + "/movie/{}/recommendations"
        p = self.__default_params()
        res = requests.get(url.format(movie_id), params=p)
        res = json.loads(res.text)
        return res['results']

    def get_genres(self):
        """
        Returns a dict of IDs -> names from TMDb
        """
        url = BASE_URL + "/genre/movie/list"
        p = self.__default_params()
        res = requests.get(url, params=p)
        res = json.loads(res.text)["genres"]
        res = {x["id"]: x["name"] for x in res}
        return res
