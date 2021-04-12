from selenium import webdriver
from bs4 import BeautifulSoup

class ProtonDBWebDriver:
    def search(self, query):
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        options.add_argument('--headless')
        driver = webdriver.Chrome("/usr/lib/chromium/chromedriver", options=options)

        url = "https://www.protondb.com/search?q=" + '%20'.join(query)

        driver.get(url)
        href = ''
        try:
            linkButton = driver.find_element_by_class_name('kZnLdd')
            linkButtonA = linkButton.find_element_by_tag_name('a')
            href = linkButtonA.get_attribute('href')
        except:
            try:
                linkButton = driver.find_element_by_class_name('etrWhy')
                linkButtonA = linkButton.find_element_by_tag_name('a')
                href = linkButtonA.get_attribute('href')
            except:
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                return None

        return href