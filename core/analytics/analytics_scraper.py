import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime

def scrape_trending(url, selector):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    items = [item.get_text(strip=True) for item in soup.select(selector)]
    return items

def store_data(items, filename='trending.csv'):
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    df = pd.DataFrame(items, columns=['Trend'])
    df['Date'] = date
    df.to_csv(filename, index=False)

if __name__ == "__main__":
    sources = [
        {'url': 'https://trends.google.com', 'selector': 'div.trending-item'},
        {'url': 'https://twitter.com/explore', 'selector': 'div.trending'},
        {'url': 'https://www.tiktok.com/trending', 'selector': 'h3'},
        {'url': 'https://coinmarketcap.com', 'selector': 'p.sc-1eb5slv-0'},
        {'url': 'https://www.investing.com', 'selector': 'span.text'}
    ]
    all_trends = []
    for source in sources:
        trends = scrape_trending(source['url'], source['selector'])
        all_trends.extend(trends)
    store_data(all_trends)
