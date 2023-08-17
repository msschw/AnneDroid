import re

from bs4 import BeautifulSoup
from selenium import webdriver


class MetacriticWebDriver:
    def search(self, query):
        options = webdriver.ChromeOptions()
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--incognito")
        options.add_argument("--headless")
        driver = webdriver.Chrome("/usr/lib/chromium/chromedriver", options=options)

        baseurl = "https://www.metacritic.com"
        url = baseurl + "/search/all/" + "%20".join(query) + "/results"

        driver.get(url)
        href = ""
        title = ""
        rating = ""
        try:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            title_element = soup.find("h3", attrs={"class": "product_title basic_stat"})
            href_node = title_element.findChild()
            title = href_node.text.replace("\n", "").lstrip().strip()
            href = baseurl + href_node.attrs.get("href")
            rating_node = soup.find("span", re.compile("metascore_w medium"))
            rating = rating_node.text
        except:
            if href != "":
                return title + ": " + rating + "\n" + href
            else:
                return None

        return title + ": " + rating + "\n" + href
