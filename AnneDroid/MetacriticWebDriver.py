from selenium import webdriver
from bs4 import BeautifulSoup

class MetacriticWebDriver:
    def search(self, query):
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        options.add_argument('--headless')
        driver = webdriver.Chrome("/usr/lib/chromium/chromedriver", options=options)

        baseurl = "https://www.metacritic.com"
        url = baseurl + "/search/all/" + '%20'.join(query) + '/results'

        driver.get(url)
        href = ''
        title = ''
        rating = ''
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            titleElement = soup.find('h3', attrs={'class' : 'product_title basic_stat'})
            hrefNode = titleElement.findChild()
            title = hrefNode.text.replace('\n', '').lstrip().strip()
            href = baseurl + hrefNode.attrs.get('href')
            ratingNode = soup.find('span', attrs={'class' : 'metascore_w medium tvshow positive'})
            rating = ratingNode.text
        except:
            return None

        return title + ': ' + rating + '\n' + href
