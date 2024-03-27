import bs4
import difflib
import langdetect
import numpy as np
import re
import wikipedia

from bs4 import BeautifulSoup
from constants import TRANSLATE_CATEGORIES, GENRE, SORTIE, EN, FR, LANG
from typing import Optional


def search_potential_articles(titles: list[str], k: int = 5) -> dict[str, list[str]]:
    """Search potential articles corresponding to titles in the list using the Wikipedia Python API.
    It will search the french wikipedia for title that are detected in french and the english one for any other language.

    Note : This is to prevent querying languages that I dont speak as my movie list mainly contain these two languages.
    We might want to use a more accurate language detector.

    Args:
        titles (list[str]): List of the movie titles.

    Returns:
        dict[str, list[str]]: _description_
    """

    potential_articles = {}
    for title in titles:
        if langdetect.detect(title) == FR:
            wikipedia.set_lang(FR)
            wiki_lang = FR
        else:
            wikipedia.set_lang(EN)
            wiki_lang = EN

        articles = wikipedia.search(title + "_(film)", results=k)
        potential_articles[title] = (articles, wiki_lang)
    return potential_articles


def check_title_overlap(title: str, target: str) -> bool:
    """Check if the title is contained in the target or the other way around.

    Args:
        title (str): The seach title.
        target (str): The page title that we want to compare it to.

    Returns:
        bool: True if title is totally contained in target or the other way around.
    """
    return title.lower() in target.lower() or target.lower() in title.lower()


def get_most_likely_article(
    title: str, potential_articles: list[str], verbose: bool = True
) -> Optional[str]:
    """Determines the most likely article name from a list of potential articles.
    Use string similarity and heuristics to determine the best match.

    Args:
        title (str): The title we search.
        potential_articles (list[str]): The list of articles retrieved on Wikipedia.
        verbose (bool, optional): Toggle detailed print in case of error. Defaults to True.

    Returns:
        Optional[str]: The most likely article title or None if the answer is too unsure.
    """
    if not potential_articles:
        return None

    similarities = [
        difflib.SequenceMatcher(None, title, p).ratio() for p in potential_articles
    ]
    highest_similartiy_index = np.argmax(similarities)

    # If the title is completely contained in page 0, return it.
    top_article = potential_articles[0]
    if check_title_overlap(title, top_article):
        return top_article

    # If we're confident enough in the first page and it either mentions 'film' or has the highest similarity in the list.
    if similarities[0] >= 0.6:
        #
        if (
            "film" in top_article
            or similarities[0] >= similarities[highest_similartiy_index]
        ):
            return top_article

    # If none of the pages are similar to the query, assume that there is a spelling error and return None
    if similarities[highest_similartiy_index] < 0.6:
        if verbose:
            print(
                f"The retrived pages for {title} are pretty uncertain. Try changing the spelling to one of the following : \n {potential_articles}"
            )
        return None
    return potential_articles[highest_similartiy_index]


def detect_genre_for_en_lang(page: wikipedia.wikipedia.WikipediaPage) -> Optional[str]:
    summary = page.summary[:256].split(" ")
    genre = None
    if "film" in summary:
        idx_film = summary.index("film")
        if "American" in summary:
            genre = " ".join(summary[summary.index("American") + 1 : idx_film])
        else:
            genre = " ".join(summary[summary.index("film") - 4 : summary.index("film")])
    return genre


def scrape_wikipedia_article(title: str, article: str, lang: str):

    # Set wikipedia to the correct lang.
    wikipedia.set_lang(lang)

    # Get the page off wikipedia
    page = wikipedia.page(title=article, auto_suggest=False)

    # Parse it using bs4
    good_soup = BeautifulSoup(page.html(), "html.parser")

    # Look for the 'infobox_v3' div of the page which is the movie header.
    # We have different tags that we look for depending on the language
    if lang == FR:
        tag_type = "div"
        infobox_class = "infobox_v3"
    else:
        tag_type = "table"
        infobox_class = "infobox"
    infoboxes = good_soup.find_all(tag_type, class_=infobox_class)
    if len(infoboxes) > 0:
        infos = scrape_infobox(infoboxes[0], lang)

        if lang == EN:
            genre = detect_genre_for_en_lang(page)
            infos[GENRE] = [genre]

        infos = clean_outputs(infos)
        print(f"Retrieved informations for {title} !")
    else:
        print(f"Could not find any infoboxes on the page of {title} !")
        return {}
    return infos


def scrape_infobox(infobox: bs4.element.Tag, lang: str) -> dict:
    """Generate the key-value mapping of the informations found in

    Args:
        infobox (bs4.element.Tag): _description_
        lang (str): _description_

    Returns:
        _type_: _description_
    """

    tr_in_info_box = infobox.find_all("tr")
    mapping = {}
    for tr in tr_in_info_box:
        th = tr.find("th")
        if not th:
            continue
        key = th.text.strip()
        entries = tr.find("td")
        if not entries:
            continue
        links = entries.find_all("a" if lang == FR else "li")
        values = []
        for link in links:
            values.append(link.text.strip())

        if len(values) == 0:
            values.append(entries.text.strip())

        mapping[key] = values
    mapping[LANG] = [lang]
    return mapping


def clean_outputs(infos: dict[str, any]) -> dict[str, any]:
    """Clean the output dictionary so that they all have a corresponding format

    Args:
        infos (dict): dictionary containing the corresponding information retrieved for a given movie

    Returns:
        dict[str, any]: cleaned dictionary
    """

    # Rename only one Genre Category
    if "Genres" in infos.keys():
        infos[GENRE] = infos.pop("Genres")

    if infos[LANG][0] == EN:
        keys = list(infos.keys())
        for key in keys:
            if key in TRANSLATE_CATEGORIES:
                infos[TRANSLATE_CATEGORIES[key]] = infos.pop(key)

    # Regex match year only in release date
    if SORTIE in infos.keys():
        infos[SORTIE] = [re.search(r"\d+\d+\d+\d+", infos[SORTIE][0]).group(0)]

    # Clean the outputs
    for key, value in infos.items():
        if type(value) == str or not value:
            continue

        infos[key] = [re.sub(r"\[.*\]", "", v) for v in value if v and v != ""]
    return infos
