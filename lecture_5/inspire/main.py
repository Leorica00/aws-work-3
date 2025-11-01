import json
from typing import Optional
from urllib.parse import quote
from urllib.request import Request, urlopen

headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
}

def get_quote(author: Optional[str] = None):
    """Generic function to fetch data from the quotes API."""
    base_url = "https://api.quotable.kurokeita.dev/api/quotes/random"
    url = f"{base_url}?author={quote(author)}" if author else base_url

    result = {}
    try:
        with urlopen(Request(url, data=None, headers=headers)) as response:
            result = json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching quote: {e}")

    return result


def print_quote(quote: dict):
    """Print the quote in a formatted way."""
    print(quote["quote"]["content"])
    print("---")
    print(quote["quote"]["author"]["name"])


def main():
    print_quote(get_quote())


if __name__ == "__main__":
    main()
