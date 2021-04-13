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
                return None

        result = href
        rating = 'Garbage'
        try:
            driver.get(href)
            ratingSpan = driver.find_element_by_class_name('BJNpc')
            rating = ratingSpan.text
        except:
            try:
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                ratingElement = soup.find('span', attrs={'class' : 'Summary__GrowingSpan-sc-18cac2b-1 BJNpc'})
                rating = ratingElement.text
            except:
                rating = 'Fail'

        return ' '.join(query) + ': ' + rating + '\n' + href
