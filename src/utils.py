import pandas as pd

from constants import (
    REALISATEUR,
    GENRE,
    ACTEURS,
    SORTIE,
    PAYS_PROD,
    DUREE,
    OUTPUT_CATEGORIES,
)


def read_input_movies(file: str = "input.txt") -> list[str]:
    """Read a list of movies from a give text file.

    Args:
        file (str, optional): The path to the file. Defaults to "input.txt".

    Returns:
        list[str]: The list of all movies specified in the text file.
    """
    with open(file) as f:
        lines = f.readlines()
    return [line.strip() for line in lines]


# Post processing
def convert_duration(duration):
    if duration:
        mins = duration.replace("\xa0", " ").split(" ")[0]
        try:
            int_mins = int(mins)
            display_hours = int_mins // 60
            display_mins = int_mins % 60
            display_mins = (
                f"0{display_mins}" if display_mins < 10 else f"{display_mins}"
            )
            return (
                f"{display_hours}h{display_mins}"
                if display_hours > 0
                else f"{display_mins}mins"
            )
        except ValueError:
            return None
    else:
        return None


def get_informations(movie_infos, categorie, index: int = None):
    # Check that the categorie exist in the retrived informations o.w return None
    if categorie not in movie_infos:
        return None

    #
    info = movie_infos[categorie]
    if index is None:
        return info

    if len(info) > index:
        return info[index]

    return None


def movie_to_df_row(title, movie_infos):
    # Get values then aggregate
    realisation = get_informations(movie_infos, REALISATEUR, 0)
    genre = get_informations(movie_infos, GENRE, 0)
    premier_role = get_informations(movie_infos, ACTEURS, 0)
    second_role = get_informations(movie_infos, ACTEURS, 1)
    sortie = get_informations(movie_infos, SORTIE, 0)
    duree = get_informations(movie_infos, DUREE, 0)
    duree = convert_duration(duree)
    pays_production = get_informations(movie_infos, PAYS_PROD, 0)

    return [
        title,
        None,  # Note
        None,  # Remarques
        realisation,
        genre,
        premier_role,
        second_role,
        sortie,
        duree,
        None,  # Rythme
        None,  # Accessibilité
        None,  # Violence
        None,  # Recompenses TODO: add this
        pays_production,
    ]


def write_movies_df(movies):

    processed_movies = []

    for movie, infos in movies.items():
        processed_movies.append(movie_to_df_row(movie, infos))

    return pd.DataFrame(processed_movies, columns=OUTPUT_CATEGORIES)


def save_as_excel(df: pd.DataFrame, file: str = "output.xlsx"):
    df.to_excel(file, index=False)
