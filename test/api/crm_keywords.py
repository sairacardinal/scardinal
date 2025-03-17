from bs4 import BeautifulSoup


def get_customer_ids_from_html(html_content):
    """
    Extracts the first <td> (Customer ID) from each <tr> in the customers table.

    :param html_content: Full HTML content as a string.
    :return: List of customer IDs as strings.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Find the table with customers
    table = soup.find("table", class_="table table-bordered")
    if not table:
        return []

    customer_ids = []
    rows = table.find("tbody").find_all("tr")  # Get all table rows

    for row in rows:
        first_td = row.find("td")  # First <td> in each row
        if first_td:
            customer_ids.append(first_td.text.strip())  # Extract text and clean it

    return customer_ids
