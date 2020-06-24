# Movie/TV suggestor based on IMDb ratings and TMDb recommendations

I like to log my movies and series, so I use the IMDb app mostly. 
Unfortunately, I haven't found any good TMDb apps and I want my lists easily accessible, but I do want you use the nice API from TMDb (they have a nice website too).

So here's a script that uses your ratings (ratings.csv that can be manually downloaded from your IMDb account), and a pseudo-scientific mathematical formula to give recommendations with help from TMDb's suggestions.

Here's what it looks like:

``` bash
Note: All queries default to movie results.
Note: Personalized suggestions doesn't include average rating when calculating suggestions.
Options:
	's[uggest] [tv]' 	- preview <media_type>_suggestions.txt
	's[uggest] [tv] p[ersonalized]' 	- preview <media_type>_suggestions_p.txt
	'g[enre]' 	- show genre options
	'[tv] [-]<genre>, ...' 	- preview <media_type>_suggestions.txt filtered by genre[s]
	'u[pdate]' 	- update ratings.csv from imdb and generate suggestion files
Enter command: 
```
ignore the messy tabs...

A small sample of the suggestions preview:

```txt
Star Wars (1977) (match 1.42, relevance 8)
        Genres: ['action', 'adventure', 'science fiction']
        Popularity: 46.381
        Rating: 8.2
        https://www.themoviedb.org/movie/11
The Empire Strikes Back (1980) (match 1.40, relevance 10)
        Genres: ['action', 'adventure', 'science fiction']
        Popularity: 25.098
        Rating: 8.4
        https://www.themoviedb.org/movie/1891
Raiders of the Lost Ark (1981) (match 1.33, relevance 11)
        Genres: ['action', 'adventure']
        Popularity: 25.331
        Rating: 7.9
        https://www.themoviedb.org/movie/85
Spider-Man (2002) (match 1.32, relevance 7)
        Genres: ['action', 'fantasy']
        Popularity: 28.048
        Rating: 7.1
        https://www.themoviedb.org/movie/557
Indiana Jones and the Last Crusade (1989) (match 1.31, relevance 11)
        Genres: ['action', 'adventure']
        Popularity: 22.113
        Rating: 7.8
        https://www.themoviedb.org/movie/89
Ice Age (2002) (match 1.31, relevance 33)
        Genres: ['adventure', 'animation', 'comedy', 'family']
        Popularity: 21.531
        Rating: 7.3
        https://www.themoviedb.org/movie/425
No Country for Old Men (2007) (match 1.30, relevance 12)
        Genres: ['crime', 'drama', 'thriller']
        Popularity: 22.671
        Rating: 7.9
        https://www.themoviedb.org/movie/6977
[...]
```
(of course I've seen most of these, just want to re-watch to give proper rating...)

I've tried to keep the script fairly modular so that it should be easy to modify. 
I suggest that you play around with the scoring formula if you want other results.

## Requirements

* less (unix) or more (windows, untested) - for previewing in terminal
* Uses ratings.csv fetched from IMDb
* TMDb account with API key
