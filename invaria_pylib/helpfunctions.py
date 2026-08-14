import requests
from bs4 import BeautifulSoup


def get_soup(url: str, session: requests.Session) -> BeautifulSoup:
    """Get the content of a web page.

    Parameters
    ----------
    url
        The url of the web page that should be retrieved.
    session
        An existing session.

    Returns
    -------
        The BeautifulSoup representation of the web page.
    """
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def snake_case2camel_case(string: str) -> str:
    """Converts a snake_case string to a camelCase one."""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])
