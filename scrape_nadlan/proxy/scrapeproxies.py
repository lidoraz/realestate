import json

import requests
from bs4 import BeautifulSoup
import concurrent.futures

#get the list of free proxies
def getProxies():
    r = requests.get('https://free-proxy-list.net/')
    soup = BeautifulSoup(r.content, 'html.parser')
    table = soup.find('tbody')
    proxies = []
    for row in table:
        if row.find_all('td')[4].text =='elite proxy':
            proxy = ':'.join([row.find_all('td')[0].text, row.find_all('td')[1].text])
            proxies.append(proxy)
        else:
            pass
    return proxies

def extract(proxy, timeout=2):
    #this was for when we took a list into the function, without conc futures.
    #proxy = random.choice(proxylist)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}
    try:
        #change the url to https://httpbin.org/ip that doesnt block anything
        r = requests.get('https://httpbin.org/ip', headers=headers, proxies={'http' : proxy,'https': proxy}, timeout=timeout)
        location = find_location(proxy)
        if location != 'Failed':
            print(proxy, r.json(), r.status_code, location)
            return proxy
    except (requests.ConnectionError, requests.ReadTimeout, json.JSONDecodeError) as err:
        return None
        # print(repr(err))
    return None


def find_location(proxy):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}
    try:
        r = requests.get('https://mylocation.org', headers=headers, proxies={'http': proxy, 'https': proxy},
                         timeout=2)
    except:
        return "Failed"
    if r.status_code == 200:
        country = BeautifulSoup(r.content, 'html.parser').find(attrs={"class": "info"}).find_all('td')[7].text
        return country
    else:
        return "Failed"


def run():

    #print(len(proxylist))

    #check them all with futures super quick
    known_proxies = {}

    while True:
        proxylist = getProxies()
        with concurrent.futures.ThreadPoolExecutor() as executor:
                res = executor.map(extract, proxylist)
                res = [x for x in res if x is not None]
        print(res)

    trusted_countries = ['Netherlands', 'Indonesia']
    from datetime import datetime
    while True:
        print("again")
        for p in res:
            country = find_location(p)
            if country != "Failed":
                # known_proxies.get(p, '')
                print(p, country, known_proxies.get(p, ''))
                if p not in known_proxies:
                    known_proxies[p] = datetime.now()
            else:
                if p in known_proxies:
                    print(f"Removing {p} from set")
                    known_proxies[p] = "FAILED"

    # with open('working_proxies.csv', 'w') as f:
    #     for r in res:
    #         print(r, file=f)

if __name__ == '__main__':
    run()