from pymongo import MongoClient
import urllib3
from bs4 import BeautifulSoup
import re

################################
client = MongoClient("ds155509.mlab.com", 55509)
db = client['huplib2']
db.authenticate('daoan', '0903293343')
oxford = db['oxford']
pending = db['pending']

###############
http = urllib3.PoolManager()
query = 'concern_1'
URL = 'http://www.oxfordlearnersdictionaries.com/definition/english/' + query


def getSoup(url):
    try:
        r = http.request('GET', url)
    except:
        return None
    try:
        bsObj = BeautifulSoup(r.data, 'lxml')
    except:
        return None
    return bsObj


def getLink(soup):
    try:
        pattern = "^(http:\/\/www.oxfordlearnersdictionaries.com\/definition\/english\/)((?!#).)*$"
        li = soup.findAll('a', href=re.compile(pattern))
    except:
        return None
    return [link.attrs['href'] for link in li]


def linkToQuery(link):
    _query = [e.split('/')[-1] for e in link]
    return list(set(_query))


def getWord(soup):
    return soup.find('h2', class_='h').get_text()


while True:
    _Soup = getSoup(URL)
    if _Soup is None:
        continue
    Word = getWord(_Soup)
    lst_query = linkToQuery(getLink(_Soup))

    pending.update({'query': query}, {'$set': {'status': 'ok'}})
    if query in lst_query:
        lst_query.remove(query)

    for q in lst_query:
        doc = pending.find_one({'query': q})
        if doc is None:
            pending.insert_one({'query': q, 'status': 'pending'})

    document = oxford.find_one({'word': Word})
    if document is None:
        oxford.insert_one({'word': Word, 'query': [query]})
    elif query not in document['query']:
        one_set = set(document['query'])
        one_set.add(query)
        oxford.update({'word': Word}, {'$set': {'query': list(one_set)}})

    doc_q = pending.find_one({'status': 'pending'})
    if doc_q is not None:
        query = doc_q['query']
        URL = 'http://www.oxfordlearnersdictionaries.com/definition/english/' + query
    else:
        break
