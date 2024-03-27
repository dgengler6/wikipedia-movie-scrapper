import typer

from utils import read_input_movies, write_movies_df, save_as_excel
from scrape import (
    search_potential_articles,
    get_most_likely_article,
    scrape_wikipedia_article,
)


def main(intput_file: str = "../io/input.txt", output_file: str = "../io/output.xlsx"):

    # Get movies titles from the input file.
    titles = read_input_movies(file=intput_file)

    # Get the potential articles for each movie
    potential_articles = search_potential_articles(titles)

    cumul = 0
    movies_infos = {}
    for title, (page_list, lang) in potential_articles.items():
        most_likely_article = get_most_likely_article(title, page_list)

        if not most_likely_article:
            continue

        # if cumul > 5:
        #     break
        # cumul += 1

        infos = scrape_wikipedia_article(title, most_likely_article, lang)
        movies_infos[title] = infos

        # print(title, most_likely_article, lang)
        # print(movies_infos[title])
    print("Done Retrieving Informations!")
    movies_df = write_movies_df(movies_infos)

    save_as_excel(movies_df, output_file)
    print(f"Informations written in file {output_file}")


if __name__ == "__main__":
    typer.run(main)
