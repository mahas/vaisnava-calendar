import sys
import os
import os.path
import flask
import logging
import io
import threading
import json
import unicodedata
import re
from collections import OrderedDict
from flask import jsonify, request, Response

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from .GCLocationList import FindLocation, FindLocations, GetLocationsForCountry
from .GCCountry import GetCountries
from .GCGregorianDate import GCGregorianDate, Today
from .TCalendar import TCalendar
from .GCLocation import GCLocation

# Clean, thread-safe in-memory cache with size limiting
class SimpleCache:
    def __init__(self, maxsize=100):
        self.cache = OrderedDict()
        self.maxsize = maxsize
        self.lock = threading.Lock()
        
    def get(self, key):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
            
    def set(self, key, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.maxsize:
                self.cache.popitem(last=False)

calendar_cache = SimpleCache(maxsize=100)
search_cache = SimpleCache(maxsize=100)

EKADASHI_SYNONYMS = {
    "varuthini": ["varuthini", "vaisakhakrishna", "caitrakrishna"],
    "mohini": ["mohini", "vaisakhashukla"],
    "apara": ["apara", "jyesthakrishna"],
    "pandavanirjala": ["nirjala", "bhima", "bhimanirjala", "pandava", "jyesthashukla"],
    "yogini": ["yogini", "asadhakrishna"],
    "sayana": ["sayana", "devashayana", "harisayana", "asadhashukla"],
    "kamika": ["kamika", "sravanakrishna"],
    "pavitraropana": ["pavitraropana", "pavitra", "sravanashukla"],
    "annada": ["annada", "aja", "bhadrapadakrishna"],
    "parsva": ["parsva", "parivartini", "vamana", "bhadrapadashukla"],
    "indira": ["indira", "asvinakrishna"],
    "pasankusa": ["pasankusa", "padmanabha", "asvinashukla"],
    "rama": ["rama", "kartikakrishna"],
    "utthana": ["utthana", "devotthana", "prabodhini", "kartikashukla"],
    "utpanna": ["utpanna", "margasirsakrishna"],
    "moksada": ["moksada", "mokshada", "margasirsashukla"],
    "saphala": ["saphala", "pausakrishna"],
    "putrada": ["putrada", "pausashukla"],
    "sattila": ["sattila", "sattila", "maghakrishna"],
    "bhaimi": ["bhaimi", "jaya", "varaha", "maghashukla"],
    "vijaya": ["vijaya", "phalgunakrishna"],
    "amalaki": ["amalaki", "amalakivrata", "phalgunashukla"],
    "papamocani": ["papamocani", "papamochani", "caitrakrishna"],
    "kamada": ["kamada", "caitrashukla"],
    "parama": ["parama", "adhikakrishna", "purusottamakrishna"],
    "padmini": ["padmini", "adhikashukla", "purusottamashukla"]
}

def simplify(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    text = text.lower()
    text = text.replace("sh", "s")
    text = text.replace("ch", "c")
    text = text.replace("ri", "r")
    text = text.replace("ee", "i")
    text = text.replace("oo", "u")
    text = text.replace("aa", "a")
    text = text.replace("ou", "au")
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

# Global list of possible names for query validation
ALL_POSSIBLE_SIMPLIFIED_NAMES = []
ALL_POSSIBLE_NAMES_LOADED = False
load_lock = threading.Lock()

def ensure_possible_names_loaded():
    global ALL_POSSIBLE_SIMPLIFIED_NAMES, ALL_POSSIBLE_NAMES_LOADED
    if ALL_POSSIBLE_NAMES_LOADED:
        return
    with load_lock:
        if ALL_POSSIBLE_NAMES_LOADED:
            return
        
        names = []
        
        # Load strings.json
        strings_path = os.path.join(os.path.dirname(__file__), 'res', 'strings.json')
        if os.path.exists(strings_path):
            try:
                with open(strings_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                    for val in data.values():
                        names.append(simplify(val))
            except Exception as e:
                print("Error loading strings.json for validation:", e)
                
        # Load events.json
        events_path = os.path.join(os.path.dirname(__file__), 'res', 'events.json')
        if os.path.exists(events_path):
            try:
                with open(events_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        names.append(simplify(item.get('text', '')))
            except Exception as e:
                print("Error loading events.json for validation:", e)
                
        # Add all synonyms
        for synonyms in EKADASHI_SYNONYMS.values():
            for syn in synonyms:
                names.append(simplify(syn))
                
        ALL_POSSIBLE_SIMPLIFIED_NAMES = list(set([n for n in names if n]))
        ALL_POSSIBLE_NAMES_LOADED = True

app = flask.Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok"})

@app.route('/countries', methods=['GET'])
def getListCountries():
    return jsonify(GetCountries())

@app.route('/find-location', methods=['GET','POST'])
def findLocation():
    if request.method == 'GET':
        name = request.args.get('name')
        country = request.args.get('country')
        e, s, c = FindLocations(name, country)
        obj = {
            'EQUALS': [a.data() for a in e],
            'STARTS': [a.data() for a in s],
            'CONTAINS': [a.data() for a in c]
        }
        return jsonify(obj)
    elif request.method == 'POST':
        content = request.get_json()
        name = None
        country = None
        if 'name' in content:
            name = content['name']
        if 'country' in content:
            country = content['country']
        e, s, c = FindLocations(name, country)
        obj = {
            'EQUALS': [a.data() for a in e],
            'STARTS': [a.data() for a in s],
            'CONTAINS': [a.data() for a in c]
        }
        return jsonify(obj)

@app.route('/calendar', methods=['GET','POST'])
def getCalendar():
    loca = {}
    date = {}
    period = None
    fmt = None
    req_data = None
    if request.method == 'GET':
        req_data = request.args
    elif request.method == 'POST':
        req_data = request.json
    else:
        return flask.make_response('Unknown method', 500)

    loca['city'] = req_data.get('city')
    loca['country'] = req_data.get('country')
    loca['latitude'] = req_data.get('latitude')
    loca['longitude'] = req_data.get('longitude')
    loca['tzname'] = req_data.get('tzname')
    date['year'] = req_data.get('year')
    date['month'] = req_data.get('month')
    date['day'] = req_data.get('day')
    period = req_data.get('period')
    fmt = req_data.get('format')
    
    if loca['latitude'] is None and loca['longitude'] is not None \
       or loca['latitude'] is not None and loca['longitude'] is None:
       return flask.make_response('Either both LATITUDE,LONGITUDE are valid or none of them', 500)

    if loca['city'] is None:
        return flask.make_response('city: - Name of location must be specified.', 500)

    if loca['country'] is None:
        return flask.make_response('country: Name of country must be specified.', 500)

    if loca['latitude'] is None:
        sp = FindLocation(city=loca['city'], country=loca['country'])
        if sp is None:
            return flask.make_response('Location with name \'{}\', country \'{}\' is not found in database.'.format(loca['city'], loca['country']), 500)
        loca['latitude'] = sp.m_fLatitude
        loca['longitude'] = sp.m_fLongitude
        loca['tzname'] = sp.m_strTimeZone
        loca['location'] = sp
    else:
        loca['latitude'] = float(loca['latitude'])
        loca['longitude'] = float(loca['longitude'])

    if loca['tzname'] is None:
        return flask.make_response('tz: Name of timezone must be specified.', 500)
    
    if date['year'] is None:
        d = Today()
        date['year'] = d.year
    else:
        date['year'] = int(date['year'])

    if date['month'] is None:
        date['month'] = 1
    else:
        date['month'] = int(date['month'])

    if date['day'] is None:
        date['day'] = 1
    else:
        date['day'] = int(date['day'])

    if period is None:
        return flask.make_response('p: Time period must be specified.', 500)
    try:
        period = int(period)
    except:
        return flask.make_response('p: Time period is number of days (integer number).', 500)
    if period<1:
        return flask.make_response('p: Time period must be greater than 0 days.', 500)
    if period>3653:
        return flask.make_response('p: Time period must be lower than 3654 days.', 500)

    # Caching key
    cache_key = (
        loca['city'], loca['country'], loca['latitude'], loca['longitude'], loca['tzname'],
        date['year'], date['month'], date['day'], period, fmt
    )
    cached_val = calendar_cache.get(cache_key)
    if cached_val is not None:
        if fmt in ['txt', 'text', 'plain']:
            return Response(cached_val, mimetype='text/plain')
        elif fmt == 'html':
            return Response(cached_val, mimetype='text/html')
        elif fmt == 'html-table':
            return Response(cached_val, mimetype='text/html')
        elif fmt == 'xml':
            return Response(cached_val, mimetype='text/xml')
        else:
            return jsonify(cached_val)

    tc = TCalendar()
    date2 = GCGregorianDate(year=date['year'], month=date['month'], day=date['day'])
    location = loca.get('location')
    if location is None:
        location = GCLocation(data={
            'city': loca['city'],
            'country': loca['country'],
            'latitude': loca['latitude'],
            'longitude': loca['longitude'],
            'tzname': loca['tzname']
        })
    tc.CalculateCalendar(location,date2,period)

    wf = io.StringIO()

    if fmt == 'txt' or fmt=='text' or fmt=='plain':
        tc.write(wf, format='plain')
        res_val = wf.getvalue()
        calendar_cache.set(cache_key, res_val)
        return Response(res_val, mimetype='text/plain')
    elif fmt=='html':
        tc.write(wf)
        res_val = wf.getvalue()
        calendar_cache.set(cache_key, res_val)
        return Response(res_val, mimetype='text/html')
    elif fmt=='html-table':
        tc.write(wf, layout='table')
        res_val = wf.getvalue()
        calendar_cache.set(cache_key, res_val)
        return Response(res_val, mimetype='text/html')
    elif fmt=='xml':
        tc.write(wf, format='xml')
        res_val = wf.getvalue()
        calendar_cache.set(cache_key, res_val)
        return Response(res_val, mimetype='text/xml')
    else:
        res_val = tc.get_json_object()
        calendar_cache.set(cache_key, res_val)
        return jsonify(res_val)

@app.route('/search-event', methods=['GET','POST'])
def searchEvent():
    req_data = None
    if request.method == 'GET':
        req_data = request.args
    elif request.method == 'POST':
        req_data = request.json
    else:
        return flask.make_response('Unknown method', 500)

    query = req_data.get('query')
    if not query:
        return flask.make_response('query: Search query must be specified.', 400)

    loca = {}
    loca['city'] = req_data.get('city')
    loca['country'] = req_data.get('country')
    loca['latitude'] = req_data.get('latitude')
    loca['longitude'] = req_data.get('longitude')
    loca['tzname'] = req_data.get('tzname')
    
    if loca['latitude'] is None and loca['longitude'] is not None \
       or loca['latitude'] is not None and loca['longitude'] is None:
       return flask.make_response('Either both LATITUDE,LONGITUDE are valid or none of them', 500)

    if loca['city'] is None:
        return flask.make_response('city: - Name of location must be specified.', 500)

    if loca['country'] is None:
        return flask.make_response('country: Name of country must be specified.', 500)

    if loca['latitude'] is None:
        sp = FindLocation(city=loca['city'], country=loca['country'])
        if sp is None:
            return flask.make_response('Location with name \'{}\', country \'{}\' is not found in database.'.format(loca['city'], loca['country']), 500)
        loca['latitude'] = sp.m_fLatitude
        loca['longitude'] = sp.m_fLongitude
        loca['tzname'] = sp.m_strTimeZone
        loca['location'] = sp
    else:
        loca['latitude'] = float(loca['latitude'])
        loca['longitude'] = float(loca['longitude'])

    if loca['tzname'] is None:
        return flask.make_response('tz: Name of timezone must be specified.', 500)

    start_year = req_data.get('year')
    start_month = req_data.get('month')
    start_day = req_data.get('day')

    if start_year is None:
        d = Today()
        start_year = d.year
        start_month = d.month
        start_day = d.day
    else:
        start_year = int(start_year)
        start_month = int(start_month) if start_month is not None else 1
        start_day = int(start_day) if start_day is not None else 1

    count = req_data.get('count')
    if count is None:
        count = 5
    else:
        try:
            count = int(count)
        except:
            count = 5
    if count < 1:
        count = 1
    if count > 20:
        count = 20

    cache_key = (
        query, loca['city'], loca['country'], loca['latitude'], loca['longitude'], loca['tzname'],
        start_year, start_month, start_day, count
    )
    cached_val = search_cache.get(cache_key)
    if cached_val is not None:
        return jsonify(cached_val)

    # Pre-validation step for early empty return (Instant Response for typos / non-existent)
    ensure_possible_names_loaded()
    simplified_query = simplify(query)
    is_possible = False
    for name in ALL_POSSIBLE_SIMPLIFIED_NAMES:
        if simplified_query in name:
            is_possible = True
            break
            
    if not is_possible:
        response_data = {
            'query': query,
            'location': {
                'city': loca['city'],
                'country': loca['country'],
                'latitude': loca['latitude'],
                'longitude': loca['longitude'],
                'tzname': loca['tzname']
            },
            'matches': []
        }
        search_cache.set(cache_key, response_data)
        return jsonify(response_data)

    location = loca.get('location')
    if location is None:
        location = GCLocation(data={
            'city': loca['city'],
            'country': loca['country'],
            'latitude': loca['latitude'],
            'longitude': loca['longitude'],
            'tzname': loca['tzname']
        })

    matches = []
    current_date = GCGregorianDate(year=start_year, month=start_month, day=start_day)

    max_years = 6
    years_searched = 0

    while len(matches) < count and years_searched < max_years:
        tc = TCalendar()
        tc.CalculateCalendar(location, current_date, 366)
        
        for day in tc.days_iter():
            day_dict = dict(day)
            ekadashi_name = day_dict.get('ekadashiName', '')
            matched_text = None
            
            # Check ekadashi name and synonyms
            if ekadashi_name:
                simp_ekadashi = simplify(ekadashi_name)
                if simplified_query in simp_ekadashi:
                    matched_text = ekadashi_name
                else:
                    # Check synonyms list
                    for base, synonyms in EKADASHI_SYNONYMS.items():
                        if base in simp_ekadashi:
                            for syn in synonyms:
                                if simplified_query in simplify(syn):
                                    matched_text = f"{ekadashi_name} ({syn.title()})"
                                    break
                            if matched_text:
                                break

            # If not matched by Ekadashi name, check events
            if not matched_text:
                events = day_dict.get('events', [])
                for ev in events:
                    ev_text = ev.get('text', '')
                    if simplified_query in simplify(ev_text):
                        matched_text = ev_text
                        break
            
            if matched_text:
                date_val = day_dict.get('date')
                already_matched = False
                for m in matches:
                    md = m['date']
                    if md['year'] == date_val['year'] and md['month'] == date_val['month'] and md['day'] == date_val['day']:
                        already_matched = True
                        break
                
                if not already_matched:
                    matches.append({
                        'date': date_val,
                        'astrodata': day_dict.get('astrodata'),
                        'ekadashiName': ekadashi_name,
                        'fast': day_dict.get('fast', 0),
                        'events': day_dict.get('events', []),
                        'ekadashiParana': day_dict.get('ekadashiParana'),
                        'matching_event': matched_text
                    })
                    if len(matches) >= count:
                        break
        
        current_date.AddDays(366)
        years_searched += 1

    response_data = {
        'query': query,
        'location': {
            'city': loca['city'],
            'country': loca['country'],
            'latitude': loca['latitude'],
            'longitude': loca['longitude'],
            'tzname': loca['tzname']
        },
        'matches': matches
    }
    search_cache.set(cache_key, response_data)
    return jsonify(response_data)

def run_server(port=8047, host="127.0.0.1"):
    app.run(host=host, port=port)

if __name__=='__main__':
    run_server()