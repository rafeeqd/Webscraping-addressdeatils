import requests
from bs4 import BeautifulSoup, Tag
import concurrent.futures
import pandas as pd

main_urls = []
another_dict = []


def beautiful_soup(soup, url):
    """
    Extracts contact details and address information from the soup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the HTML content.
        url (str): The URL of the webpage.

    Returns:
        None
    """
    print(f"Running for url {url}")
    final_list = []
    main_dict = {}

    contact_details = soup.find_all('a', {"class": "tracker-button btn btn-block btn-outline-primary"})

    for i in contact_details:
        final_list.append({i.getText().replace("Show", '').strip(): i.get('hidden_value')})

    address = soup.find('b', string="Physical Address:")
    b_tag = address.parent

    for i in b_tag:
        if type(i) == Tag:
            if i.name != 'br':
                if i.next_sibling.string.strip():
                    final_list.append({i.getText().replace(":", ''): i.next_sibling.string.strip()})
                else:
                    if i.get('href') is not None:
                        find = i.get('href').split("&")[1].split("=")
                        final_list.append({find[0].capitalize(): find[1].capitalize()})

    for i in final_list:
        main_dict.update(i)
    another_dict.append(main_dict)


def get_page_urls(soup):
    """
    Extracts the URLs of the pages from the soup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the HTML content.

    Returns:
        None
    """
    page_urls = soup.find_all('a', {"class": "link-div"})
    for page_url in page_urls:
        main_urls.append(page_url.get('href'))


def get_total_pages(soup):
    """
    Retrieves the total number of pages from the soup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the HTML content.

    Returns:
        int: The total number of pages.
    """
    total_pages = []
    links = soup.find_all('a', {"class": "page-numbers"})

    for l in links:
        temp = l.attrs['href'].split("/")[5]
        total_pages.append(int(temp))

    return max(total_pages)


def request_method(url, get_pages=None, get_soup=None):
    """
    Performs an HTTP request to the specified URL and performs different actions based on the arguments.

    Args:
        url (str): The URL to request.
        get_pages (bool, optional): If True, retrieves the total number of pages. Defaults to None.
        get_soup (bool, optional): If True, extracts contact details and address information. Defaults to None.

    Returns:
        None or int: Returns None if get_pages or get_soup is True, otherwise returns the page URLs.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    if get_pages:
        return get_total_pages(soup)
    elif get_soup:
        beautiful_soup(soup, url)
    else:
        get_page_urls(soup)


def construct_loop_query(all_pages, query_url):
    """
    Constructs and executes multiple requests with different URLs.

    Args:
        all_pages (int): The total number of pages.
        query_url (str): The URL to query with page numbers.

    Returns:
        None
    """
    with concurrent.futures.ThreadPoolExecutor() as e:
        fut = [e.submit(request_method, query_url[:53] + str(i) + query_url[53 + 1:]) for i in range(2, all_pages + 2)]


def main():
    """
    Main function to scrape data from the website, store it in a DataFrame, and save it to an Excel file.

    Returns:
        None
    """
    url = "https://www.seniorservice.co.za/advanced-search?province=0&city=0&property_type=0&section=properties"
    query_url = "https://www.seniorservice.co.za/advanced-search/page/2/?province=0&&city=0&&property_type=0&&section=properties"

    all_pages = request_method(url, get_pages=True)
    construct_loop_query(2, query_url)

    with concurrent.futures.ThreadPoolExecutor() as e:
        fut = [e.submit(request_method, i, get_soup=True) for i in main_urls]

    df = pd.DataFrame.from_dict(another_dict)
    df.to_excel("WebScrapping.xlsx", index=False)


main()
