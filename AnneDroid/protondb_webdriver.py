from bs4 import BeautifulSoup
from selenium import webdriver


class ProtonDBWebDriver:
    def search(self, query):
        options = webdriver.ChromeOptions()
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--incognito")
        options.add_argument("--headless")
        driver = webdriver.Chrome("/usr/lib/chromium/chromedriver", options=options)

        url = "https://www.protondb.com/search?q=" + "%20".join(query)

        driver.get(url)
        href = ""
        try:
            link_button = driver.find_element_by_class_name("kZnLdd")
            link_button_a = link_button.find_element_by_tag_name("a")
            href = link_button_a.get_attribute("href")
        except:
            try:
                link_button = driver.find_element_by_class_name("etrWhy")
                link_button_a = link_button.find_element_by_tag_name("a")
                href = link_button_a.get_attribute("href")
            except:
                return None

        result = href
        rating = "Garbage"
        try:
            driver.get(href)
            rating_span = driver.find_element_by_class_name("BJNpc")
            rating = rating_span.text
        except:
            try:
                soup = BeautifulSoup(driver.page_source, "html.parser")
                rating_element = soup.find(
                    "span", attrs={"class": "Summary__GrowingSpan-sc-18cac2b-1 BJNpc"}
                )
                rating = rating_element.text
            except:
                rating = "Fail"

        return " ".join(query) + ": " + rating + "\n" + href
