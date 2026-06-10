import re
import unicodedata
from rapidfuzz import fuzz
from playwright.sync_api import sync_playwright


def normalize_key(s: str) -> str:
    s = "" if s is None else str(s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.upper()
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def clean_list(items):
    out = []
    for x in items:
        x = re.sub(r"\s+", " ", str(x)).strip()
        if not x:
            continue
        if "INCONNU" in x.upper():
            continue
        if x not in out:
            out.append(x)
    return out


def parse_sacem_detail(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    title = ""
    authors = []
    composers = []
    publishers = []
    sub_publishers = []
    performers = []
    iswc = ""

    if "Retour aux résultats" in lines:
        idx = lines.index("Retour aux résultats")
        if idx + 1 < len(lines):
            title = lines[idx + 1]

    for line in lines:
        if "Code ISWC" in line:
            iswc = line.replace("Code ISWC :", "").replace("Code ISWC:", "").strip()

        if ", Compositeur-Auteur" in line:
            name = line.replace(", Compositeur-Auteur", "").strip()
            authors.append(name)
            composers.append(name)

        elif ", Compositeur" in line:
            composers.append(line.replace(", Compositeur", "").strip())

        elif ", Auteur" in line:
            authors.append(line.replace(", Auteur", "").strip())

        elif ", Editeur" in line:
            publishers.append(line.replace(", Editeur", "").strip())

        elif ", Sous Editeur" in line:
            sub_publishers.append(line.replace(", Sous Editeur", "").strip())

    if "INTERPRÈTE" in lines:
        idx = lines.index("INTERPRÈTE")
        if idx + 1 < len(lines):
            performers.append(lines[idx + 1])

    return {
        "status": "found",
        "title": title,
        "iswc": iswc,
        "authors": clean_list(authors),
        "composers": clean_list(composers),
        "publishers": clean_list(publishers),
        "sub_publishers": clean_list(sub_publishers),
        "performers": clean_list(performers),
    }


class SacemAgent:
    def __init__(self, headless: bool = False):
        self.headless = headless

    def _open_home_and_accept_cookies(self, page):
        page.goto(
            "https://repertoire.sacem.fr/",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(2000)

        try:
            page.get_by_text("Accepter les cookies").click(timeout=2000)
        except Exception:
            pass

    def _run_search(self, page, title: str, artist: str = "") -> str:
        self._open_home_and_accept_cookies(page)

        inputs = page.locator("input:visible")

        if inputs.count() < 2:
            return ""

        inputs.nth(0).fill(title)
        inputs.nth(1).fill(artist or "")

        page.locator("#searchBtn").click()

        try:
            page.wait_for_url("**/resultats**", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(3000)
        return page.locator("body").inner_text()

    def _has_results(self, body_text: str) -> bool:
        txt = body_text.lower()
        return "œuvre correspondante" in txt or "oeuvre correspondante" in txt

    def _choose_result_index(self, body_text: str, title: str, artist: str, search_mode: str) -> int:
        blocks = body_text.split("VOIR LE DÉTAIL")
        wanted_title = normalize_key(title)
        wanted_artist = normalize_key(artist)

        best_index = 0
        best_score = -1

        for i, block in enumerate(blocks[:-1]):
            block_key = normalize_key(block)

            title_score = fuzz.partial_ratio(wanted_title, block_key)

            artist_score = 0
            if wanted_artist:
                artist_score = fuzz.partial_ratio(wanted_artist, block_key)

            score = title_score

            if search_mode == "title_artist" and wanted_artist:
                score = title_score + artist_score

            if score > best_score:
                best_score = score
                best_index = i

        return best_index

    def search(self, title: str, artist: str = "") -> dict:
        title = str(title).strip()
        artist = str(artist).strip()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page(viewport={"width": 1450, "height": 900})

            body_text = self._run_search(page, title, artist)
            search_url = page.url
            search_mode = "title_artist"
            

            if not self._has_results(body_text):
                body_text = self._run_search(page, title, "")
                search_mode = "title_only_fallback"
                search_url = page.url

            detail_links = page.locator("text=VOIR LE DÉTAIL")
            count = detail_links.count()

            if count == 0:
                current_url = page.url
                browser.close()
                return {
                    "status": "not_found",
                    "title_input": title,
                    "artist_input": artist,
                    "search_mode": search_mode,
                    "url": "",
                    "raw_text": body_text[:2000],
                }

            selected_index = self._choose_result_index(body_text, title, artist, search_mode)

            if selected_index >= count:
                selected_index = 0

            detail_links.nth(selected_index).click()
            page.wait_for_timeout(5000)
            try:
                page.wait_for_url("**/detail-oeuvre/**", timeout=10000)
            except Exception:
             pass

            current_url = page.url

            if "/detail-oeuvre/" not in current_url:
                parsed = {
                    "status": "not_found",
                    "title": "",
                    "iswc": "",
                    "authors": [],
                    "composers": [],
                    "publishers": [],
                    "sub_publishers": [],
                    "performers": [],
                    "url": "",
                }
                browser.close()
                parsed["artist_input"] = artist
                parsed["title_input"] = title
                parsed["search_mode"] = search_mode
                parsed["result_count"] = count
                parsed["selected_result_index"] = selected_index
                parsed["search_url"] = search_url
                return parsed
            current_title = page.title()
            detail_text = page.locator("body").inner_text()

            parsed = parse_sacem_detail(detail_text)

            returned_title = parsed.get("title", "")
            title_score = fuzz.ratio(normalize_key(title), normalize_key(returned_title))
            parsed["title_match_score"] = title_score

            if title_score < 60:
                parsed["status"] = "not_found"
                parsed["url"] = ""
            else:
                parsed["url"] = current_url

            browser.close()

        parsed["artist_input"] = artist
        parsed["title_input"] = title
        parsed["search_mode"] = search_mode
        parsed["page_title"] = current_title
        parsed["result_count"] = count
        parsed["selected_result_index"] = selected_index
        parsed["search_url"] = search_url

        return parsed


if __name__ == "__main__":
    agent = SacemAgent(headless=False)

    result = agent.search(
        "BOOK CLUB REUNION",
        "Tom Howe",
    )

    print(result)