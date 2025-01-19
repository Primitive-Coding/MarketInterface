from Scrapers.scraper import Scraper


class YahooScraper(Scraper):
    def __init__(self):
        self.urls = {
            "gainers": "https://finance.yahoo.com/markets/stocks/gainers/",
            "losers": "https://finance.yahoo.com/markets/stocks/losers/",
        }
        super().__init__()

    def fetch_gainers(self):
        xpath = "/html/body/div[2]/main/section/section/section/article/section[1]/div/div[2]"
        data = self.read_data(xpath, wait=True)
        print(f"Data: {data}")
