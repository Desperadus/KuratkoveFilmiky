#!/usr/bin/env python3
import random
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional, Union, NewType, Iterable, Dict
import csv, urllib.request

import secret
HIGHPRIORITY_LIMIT: int = 5
DEFAULT_HIGHPRIORITY_COPY_NUM: int = 3

# f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"


class MovieFilteringStrategy(Enum):
    REMOVE = 0
    LOWER_PROBA = 1


class MovieProbabilityAssignment(Enum):
    CONSTANT = 0
    LINEAR_DECAY = 1
    EXPONENTIAL_DECAY = 2


class MovieState(Enum):
    SEEN = 0
    NOTSEEN = 1


class MoviePreference(Enum):
    SKIP = "0"
    WATCH = "1"
    PRIORITYWATCH = "*"


DEFAULT_MOVIE_PREFERENCE = MoviePreference.WATCH


@dataclass
class Movie:
    name: str
    state: MovieState


MovieSeq = Union[List[Movie], Iterable[Movie]]


@dataclass
class Person:
    name: str
    preferences: Dict[str, MoviePreference]


PersonSeq = Union[List[Person], Iterable[Person]]


def filter_absent_people(
    active_participants: List[str], people: PersonSeq
) -> Iterable[Person]:
    """
    Filter people that are not participating from the pool using
    a list of their names as an identificator
    """
    return filter(lambda person: person.name in active_participants, people)


def filter_already_seen_movies(movies: MovieSeq) -> Iterable[Movie]:
    """
    Filter movies that have already been watched by the bunch
    from the pool. This is done by using the MovieState enum
    """
    return filter(lambda movie: movie.state is not MovieState.SEEN, movies)


def copy_priority_movies(
    movies: MovieSeq,
    people: List[Person],
    k: int = DEFAULT_HIGHPRIORITY_COPY_NUM,
) -> Iterable[Movie]:
    """
    Modify the movie pool by copying movies that have
    MoviePreference.PRIORITYWATCH k-times. This is basically the easiest
    way of giving them better chances in the random pooling from a
    frequentionist point of view.
    """
    for movie in movies:
        for person in people:
            if person.preferences[movie.name] is MoviePreference.PRIORITYWATCH:
                for _ in range(k - 1):
                    yield movie
        yield movie


def filter_unwanted_movies(movies: MovieSeq, people: List[Person]) -> Iterable[Movie]:
    """
    Filter out movies that have MoviePreference.SKIP from anyone. This
    function is usually called when you specify MovieFilteringStrategy.REMOVE
    """
    for movie in movies:
        skip = False
        for person in people:
            if person.preferences[movie.name] is MoviePreference.SKIP:
                skip = True
                break
        if not skip:
            yield movie


def parse_remote_sheet_via_stdlib(
    url: str, stop_at_first_empty: bool = False, encoding: str = "utf-8"
) -> Tuple[List[Movie], List[Person]]:
    """
    Parse remote sheet using standard python libs. For the sheet download
    and decode we use `urllib` and for parsing the document itself
    the `csv` lib. It's not the prettiest of codes but it makes it possible
    to run this script without installing 3rd party libs.

    Note that whatever url you give, it needs to be converted to a csv parsable
    format.
    """
    response = urllib.request.urlopen(url)
    lines = [l.decode(encoding) for l in response.readlines()]
    cr = csv.reader(lines, quoting=csv.QUOTE_ALL)

    cols: int = -1
    movies: List[Movie] = []
    people: List[Person] = []

    # Anti-cheat measures :monkaS:
    star_count: List[int] = []

    for i, row in enumerate(cr):
        if i == 0:
            # filter out blank cols
            for name in filter(lambda name: name != "", row[2:]):
                people.append(Person(name, {}))

            cols = 2 + len(people)
            star_count = [0 for _ in range(cols)]
            continue

        movie: Movie = Movie(row[0], MovieState(int(row[1])))
        if movie.name == "":
            if stop_at_first_empty:
                break

            continue

        for j, pref in enumerate(row[2:cols]):
            if pref == "":
                pref = DEFAULT_MOVIE_PREFERENCE.value

            if MoviePreference(pref) is MoviePreference.PRIORITYWATCH:
                star_count[j] += 1

            # u can only have so much brother
            if star_count[j] >= HIGHPRIORITY_LIMIT:
                pref = MoviePreference.WATCH

            people[j].preferences[movie.name] = MoviePreference(pref)

        movies.append(movie)

    return movies, people


def suggest_movies(
    movies: List[Movie],
    num_movies: int = 1,
    proba_dist: Optional[List[float]] = None,
) -> Iterable[Movie]:
    """
    Choose randomly `num_movies` from the movies pool. You can also
    optionally specify a probability distribution of the given movies.
    """
    chosen: List[str] = []
    while len(chosen) < num_movies:
        movie = random.choices(movies, weights=proba_dist, k=1)[0]
        if movie.name not in chosen:
            chosen.append(movie.name)
            yield movie


def create_equivariant_multinomial_dist(
    population_size: int,
    boost_categories: List[int] = [],
    boost_coefs: List[float] = [],
    penalize_categories: List[int] = [],
    penalty_coefs: List[float] = [],
) -> List[float]:
    """
    Create a discrete probability distribution that has the same probability
    for each category.

    Note that it's a PDF so the integral over the whole probability space = 1.
    (to the accuracy of floating point arithmetics)
    """
    p = 1 / population_size
    return [p for _ in range(population_size)]


def create_linearly_decaying_multinomial_dist(population_size: int) -> List[float]:
    """
    Create a discrete probability distribution that has a linearly decaying
    probability for each sequential category.

    Note that it's a PDF so the integral over the whole probability space = 1.
    (to the accuracy of floating point arithmetics)
    """
    raw = [x + 1 for x in range(population_size)]
    s = sum(raw)
    return [x / s for x in raw][::-1]


def create_exponentially_decaying_multinomial_dist(population_size) -> List[float]:
    return []


def gimme_a_happy_movie_night_for_me_and_my_lil_happy_frens(
    num_movies: int,
    participants: Optional[List[str]] = None,
    remote_sheet_url: Optional[str] = None,
    filter_already_seen: bool = True,
    filtering_strategy: MovieFilteringStrategy = MovieFilteringStrategy.REMOVE,
    ignore_highpriority_pref: bool = False,
    probability_assignment: MovieProbabilityAssignment = MovieProbabilityAssignment.LINEAR_DECAY,
) -> List[Movie]:
    def _load_data() -> Tuple[List[Movie], List[Person]]:
        if remote_sheet_url is not None:
            return parse_remote_sheet_via_stdlib(remote_sheet_url)
        raise NotImplementedError("Other dataformats not yet available.")

    def _prepare_movie_population(movies: MovieSeq, people: PersonSeq) -> MovieSeq:
        if participants is not None:
            people = filter_absent_people(participants, people)

        # For the following code we have to enumerate the person list
        # since the inner loops of the generators would get exhausted
        people = list(people)

        if filter_already_seen:
            movies = filter_already_seen_movies(movies)

        # Now we create a discrete movie population
        # (freq stats yayyyyy~~~)
        if filtering_strategy is MovieFilteringStrategy.REMOVE:
            movies = filter_unwanted_movies(movies, list(people))
        elif filtering_strategy is MovieFilteringStrategy.LOWER_PROBA:
            raise NotImplementedError(
                "TODO dělej tomáši ty leňoure, dont be like this, cmon"
            )
        if not ignore_highpriority_pref:
            movies = copy_priority_movies(movies, people, k=3)  # TODO k

        return movies

    movies: MovieSeq
    people: PersonSeq
    proba_dist: List[float]
    movies, people = _load_data()

    movies = list(_prepare_movie_population(movies, people))

    population_size: int = len(movies)

    if probability_assignment is MovieProbabilityAssignment.CONSTANT:
        proba_dist = create_equivariant_multinomial_dist(population_size)
    elif probability_assignment is MovieProbabilityAssignment.LINEAR_DECAY:
        proba_dist = create_linearly_decaying_multinomial_dist(population_size)
    elif probability_assignment is MovieProbabilityAssignment.EXPONENTIAL_DECAY:
        proba_dist = create_exponentially_decaying_multinomial_dist(population_size)

    return list(suggest_movies(movies, num_movies=num_movies, proba_dist=proba_dist))


def cli_main():
    pass


if __name__ == "__main__":
    cli_main()
