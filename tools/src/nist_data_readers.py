import pathlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import tqdm

from .config_constants import CODATA_CATEGORY_BASE_URL
from .helpclasses import (
    AtomicNuclearSubcategory,
    Constant,
    ConstantCategory,
    TypstUnitLib,
)
from .helpfunctions import get_soup


def read_nist_ascii(
    nist_ascii_file: pathlib.Path, col_names_line: int = 10, start_data: int = 12
) -> list[Constant]:
    def parse_value(num: str) -> int | float:
        """Parses a string number and converts it to an integer or float."""
        if "." in num or "e" in num:
            return float(num.replace(" ", "").replace("...", ""))

        return int(num.replace(" ", ""))

    def parse_uncertainty(unc: str) -> int | float | None:
        """Parses a string uncertainty and converts it to a None value or float."""
        if "exact" in unc:
            return None

        return parse_value(unc)

    def parse_unit(unit: str, typst_pkg: TypstUnitLib = TypstUnitLib.UNIFY) -> str:
        """Parses a string unit and converts it to a typst unit."""
        # TODO: implement
        return unit

    if start_data <= col_names_line:
        raise ValueError("The column names should be above the data.")

    colnames = None
    data: list[Constant] = []
    with open(nist_ascii_file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == col_names_line - 1:
                colnames = line.split()
                continue
            if i < start_data - 1:
                continue

            if colnames is None:
                raise RuntimeError(
                    "The colnames variable should already be read and set."
                )

            line_vals = [c for c in line.strip().split("  ") if c]

            data.append(
                Constant(
                    quantity=line_vals[0],
                    symbol=None,
                    value=parse_value(line_vals[1]),
                    uncertainty=parse_uncertainty(line_vals[2]),
                    unit=None if len(line_vals) < 4 else parse_unit(line_vals[3]),
                )
            )

    return data


def read_nist_pdf(
    nist_pdf_file: pathlib.Path,
) -> None:
    """Extract Constant information from the PDF.

    Reference: https://pypdf.readthedocs.io/en/stable/user/extract-text.html

    Other libraries that might succeed:
    - Pymupdf https://pymupdf.readthedocs.io/en/latest/index.html
        - PyMuPDF extension Layout
          https://pymupdf.readthedocs.io/en/latest/pymupdf-layout/index.html
    - textract https://textract.readthedocs.io/en/stable/python_package.html
    - camelot-py
    """
    # TODO: Not sure how to map the PDF info to the ASCII info to also have the ConstantCategory
    #       Maybe https://stackoverflow.com/questions/10018679/python-find-closest-string-from-a-list-to-another-string helps
    raise NotImplementedError(
        "The further development of the function has been halted in favor of `scrape_nist`."
    )

    reader = pypdf.PdfReader(nist_pdf_file)  # pyright: ignore[reportUnreachable]

    parts = []

    def constants_body(text, user_matrix, tm_matrix, font_dict, font_size) -> None:
        header_above = 640.0
        footer_below = 50.0

        # quantity_column = 160.0
        # symbol_column = 240.0
        # value_column = 390.0
        # unit_column = 500.0

        y = tm_matrix[5]
        if footer_below < y < header_above:
            parts.append(text)

    for page in reader.pages[:2]:
        page.extract_text(visitor_text=constants_body)

    text_body = "".join(parts)

    print(text_body)

    data = []
    current_const_category: ConstantCategory | None = None
    current_atomic_nuclear_subcategory: AtomicNuclearSubcategory | None = None
    for line in text_body.splitlines():
        line = line.strip()
        if line in [cat.value for cat in ConstantCategory]:
            current_const_category = ConstantCategory(line)
            continue
        if (
            current_const_category is ConstantCategory.ATOMIC_AND_NUCLEAR
            and line.strip() in [sub_cat.value for sub_cat in AtomicNuclearSubcategory]
        ):
            current_atomic_nuclear_subcategory = AtomicNuclearSubcategory(line)
            continue

        line_vals = [c for c in line.strip().split("  ") if c]


def scrape_nist(constants: list[Constant]) -> None:
    """Scrape the NIST CODATA website to get additional information on the constants.

    Could also be used without handing over `constants` and gettings all the information from the
    web. But for now just use it to enrich existing information, as this function heavily relies on
    assumptions on the web page, that could change.

    Parameters
    ----------
    constants
        A list of constants for which the data should be scraped from the NIST homepage.

    Raises
    ------
    RuntimeError
        _description_
    """

    # HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NIST-CODATA-scraper/1.0)"}
    HEADERS = {"User-Agent": "Mozilla/5.0"}

    session = requests.Session()
    session.headers.update(HEADERS)

    # Get information on categories from website for all constants
    # URL: https://physics.nist.gov/cgi-bin/cuu/Category?view=html&<CATEGORY>
    for category in ConstantCategory:
        category_url = f"{CODATA_CATEGORY_BASE_URL}&{category.url_name}"
        cat_soup_full = get_soup(category_url, session=session)

        # It looks like the constants are all colored in #3142BD -> Filter to reduce size
        cat_soup_filtered = cat_soup_full.find_all("font", {"color": "#3142BD"})
        if len(cat_soup_filtered) != 1:
            err_msg = f"Length of filtered website is {len(cat_soup_filtered)} but should be 1. The assumption that the constant names are colored #3142BD seems to be invalid."
            raise RuntimeError(err_msg)

        # Get the link of the constants. The URL text is equal to the quantity name
        category_constants_links = {
            link.get_text(strip=True): str(link.get("href"))
            for link in cat_soup_filtered[0].find_all("a", href=True)
        }

        # Update the category and link info in the constants
        for constant in constants:
            if constant.quantity in category_constants_links:
                constant.categories.add(category)

                # Only save the relevant part
                constant_full_search_link = category_constants_links[constant.quantity]
                constant_short_search_link = constant_full_search_link.split("|")[0]
                if (
                    constant.codata_sub_url is not None
                    and constant.codata_sub_url != constant_short_search_link
                ):
                    err_msg = (
                        f"The constant CODATA sub-url has already been set to"
                        f" {constant.codata_sub_url} which differs from {constant_short_search_link}"
                        f" which has been derived in category {category}\n."
                        f"The URLs should be the same, as the category info is removed from the URL."
                    )
                    raise RuntimeError(err_msg)
                else:
                    constant.codata_sub_url = constant_short_search_link

    thread_local = threading.local()

    def get_session() -> requests.Session:
        """Helperfunction to reuse sessions in threads."""
        if not hasattr(thread_local, "session"):
            thread_local.session = requests.Session()
            thread_local.session.headers.update(
                {"User-Agent": "NIST-CODATA-scraper/1.0"}
            )

        return thread_local.session

    def get_constant_symbol(constant: Constant) -> Constant:
        session = get_session()

        const_soup = get_soup(
            constant.codata_url,
            session=session,
        )

        images = const_soup.find_all(
            "img",
            src=f"/cuu/Constants/Value/gif/{constant.codata_identifier}.gif",
        )

        if len(images) != 1:
            raise RuntimeError(
                f"Expected exactly one image for {constant}, found {len(images)}."
            )

        constant.symbol = str(
            images[0].get(
                "alt",
                "Not found when scraping website",
            )
        )

        return constant

    constants_with_url = [c for c in constants if c.codata_sub_url is not None]

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(get_constant_symbol, constant)
            for constant in constants_with_url
        ]

        for future in tqdm.tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Getting data from the NIST website",
        ):
            _ = future.result()

    print(
        f"For {len(constants) - len(constants_with_url)} of {len(constants)} constants no corresponding entry has been found on the website"
    )
