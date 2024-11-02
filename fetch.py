import copy
import os
import re

import bs4
import ftfy
import httpx
from markdownify import markdownify as md

DATE_REGEX = re.compile(
    r"\n\s*(January|February|March|April|May|June|July|August|September|October|November|December)?\s*\d{4}\b.*"
)

CHAR_REPLACEMENTS = {
    "⟨": "<",
    "⟩": ">",
    "≈": "~",  # or "≈" if you still want the symbol but in a supported font
    "̇": ".",  # Unicode combining dot, often replaced with a period or omitted
    "̀": "`",  # Unicode combining grave accent, often omitted or replaced with a backtick
}


def main():
    response = httpx.get("https://paulgraham.com/articles.html")
    response.raise_for_status()
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    title_links = [
        (link.get_text(), f"https://paulgraham.com/{link['href']}")
        for link in soup.find_all("a")
        if link.find_parent("font")
        and link.find_next_sibling("img")
        and not link["href"].startswith(
            "http"
        )  # essays are on the same domain with relative links
        and link.get_text()
        != "Revenge of the Nerds"  # this essay is not in the right format for latex
    ]
    files = []
    for i, (title, link) in enumerate(title_links, start=1):
        print(f"{title}: {link}")
        essay = httpx.get(link)
        essay.encoding = "windows-1252"
        essay.raise_for_status()
        essay_soup = bs4.BeautifulSoup(essay.text, "html.parser")
        essay_content = essay_soup.find("font", {"face": "verdana"})
        # let's replace all relative links with absolute links
        for url in essay_content.find_all("a"):
            if "href" not in url.attrs:
                url.unwrap()
            elif not url["href"].startswith("http"):
                if url["href"].startswith("#"):
                    url.unwrap()
                else:
                    url["href"] = f"https://paulgraham.com/{url['href']}"
        # remove all font tags
        for font in essay_content.find_all("font"):
            font.unwrap()

        # TODO: handle images with pandoc & latex
        for img in essay_content.find_all("img"):
            img.decompose()
        # Find all comments and keep their content (e.g.: Great Hackers)
        for comment in essay_content.find_all(
            string=lambda text: isinstance(text, bs4.Comment)
        ):
            comment.extract()
        essay_content_for_date = copy.deepcopy(essay_content)
        for table in essay_content_for_date.find_all("table"):
            table.decompose()
        date = DATE_REGEX.search(
            "\n".join(essay_content_for_date.prettify().split("\n")[:5])
        )  # date is in the first 5 lines
        if not date:
            print(f"Could not find date for {title}, skipping...")
            continue
        date = date.group()
        essay_content = essay_content.prettify().replace("<br>", "<br/>")
        essay_content = essay_content.replace(date, f"<h4>{date}</h4>\n")
        essay_content = ftfy.fix_text(essay_content)
        date = date.strip()
        for old_char, new_char in CHAR_REPLACEMENTS.items():
            essay_content = essay_content.replace(old_char, new_char)
        essay_content = "\\newpage\n\\noindent\n\n" + md(
            f"<h1>{title}</h1>\n<br/>\n<a href='{link}'>{link}</a>\n<br/>\n{essay_content}"
        )
        idx_date_title = f"{i} {date} {title}"
        safe_idx_date_title = idx_date_title.replace("/", "&").replace(" ", "_")
        output_file = os.path.join("output", "essays", f"{safe_idx_date_title}.md")
        with open(output_file, "w") as f:
            f.write(essay_content)
        files.append(output_file + "\n")
    with open(os.path.join("conf", "essays-list.txt"), "w") as f:
        f.write("".join(files))


if __name__ == "__main__":
    main()
