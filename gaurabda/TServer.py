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

@app.route('/', methods=['GET'])
def serve_index():
    web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'web')
    return flask.send_from_directory(web_dir, 'index.html')

@app.route('/<path:path>', methods=['GET'])
def serve_static_assets(path):
    if path in ['ping', 'countries', 'find-location', 'calendar', 'search-event', 'event-occurrence']:
        return flask.make_response("Not found", 404)
    web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'web')
    target_path = os.path.join(web_dir, path)
    if os.path.exists(target_path) and os.path.isfile(target_path):
        return flask.send_from_directory(web_dir, path)
    return flask.make_response(f"Resource '{path}' not found.", 404)

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

EVENT_ID_MAP = {
    "janmastami": "Janmashtami",
    "krishna_janmastami": "Janmashtami",
    "entity:concept:janmastami": "Janmashtami",
    "entity:event:krishna-janmastami": "Janmashtami",
    "urn:bhaktilib:concept:janmastami": "Janmashtami",
    "urn:bhaktilib:event:janmastami": "Janmashtami",

    "gaura_purnima": "Gaura Purnima",
    "entity:concept:gaura-purnima": "Gaura Purnima",
    "entity:event:gaura-purnima": "Gaura Purnima",

    "radhastami": "Radhastami",
    "entity:concept:radhastami": "Radhastami",
    "entity:event:radhastami": "Radhastami",

    "srila_prabhupada": "Prabhupada",
    "prabhupada": "Prabhupada",
    "entity:person:srila-prabhupada": "Prabhupada",
    "urn:bhaktilib:person:srila_prabhupada": "Prabhupada",
    "entity:event:prabhupada-appearance": "Prabhupada -- Appearance",
    "entity:event:prabhupada-disappearance": "Prabhupada -- Disappearance",

    "rama_navami": "Rama Navami",
    "entity:concept:rama-navami": "Rama Navami",
    "entity:event:rama-navami": "Rama Navami",

    "ekadasi": "Ekadashi",
    "entity:concept:ekadasi": "Ekadashi",
    "entity:event:ekadasi": "Ekadashi",

    "kartik": "Damodara",
    "entity:concept:kartik": "Damodara",
    "entity:event:kartik": "Damodara",

    "gita_jayanti": "Gita Jayanti",
    "entity:event:gita-jayanti": "Gita Jayanti",

    "entity:event:utpanna-ekadasi": "Utpanna",
    "entity:event:moksada-ekadasi": "Moksada",
    "entity:event:saphala-ekadasi": "Saphala",
    "entity:event:putrada-ekadasi": "Putrada",
    "entity:event:sattila-ekadasi": "Sattila",
    "entity:event:bhaimi-ekadasi": "Bhaimi",
    "entity:event:vijaya-ekadasi": "Vijaya",
    "entity:event:amalaki-ekadasi": "Amalaki",
    "entity:event:papamocani-ekadasi": "Papamocani",
    "entity:event:kamada-ekadasi": "Kamada",
    "entity:event:varuthini-ekadasi": "Varuthini",
    "entity:event:mohini-ekadasi": "Mohini",
    "entity:event:apara-ekadasi": "Apara",
    "entity:event:nirjala-ekadasi": "Nirjala",
    "entity:event:yogini-ekadasi": "Yogini",
    "entity:event:sayana-ekadasi": "Sayana",
    "entity:event:kamika-ekadasi": "Kamika",
    "entity:event:pavitropana-ekadasi": "Pavitropana",
    "entity:event:annada-ekadasi": "Annada",
    "entity:event:parsva-ekadasi": "Parsva",
    "entity:event:indira-ekadasi": "Indira",
    "entity:event:papankusha-ekadasi": "Papankusha",
    "entity:event:rama-ekadasi": "Rama",
    "entity:event:utthana-ekadasi": "Utthana",
    "entity:event:padmini-ekadasi": "Padmini",
    "entity:event:parama-ekadasi": "Parama"
}

@app.route('/event-occurrence', methods=['GET', 'POST'])
def eventOccurrence():
    req_data = request.args if request.method == 'GET' else (request.json or {})
    event_id = req_data.get('event_id', '')
    city = req_data.get('city', '')
    country = req_data.get('country', '')
    year_param = req_data.get('year')

    if not event_id:
        return flask.make_response(jsonify({'status': 'error', 'message': "Parameter 'event_id' is required."}), 400)
    if not city:
        return flask.make_response(jsonify({'status': 'error', 'message': "Parameter 'city' is required."}), 400)

    query_term = EVENT_ID_MAP.get(event_id)
    if not query_term:
        parts = event_id.split(':')
        query_term = parts[-1].replace('-', ' ') if parts else event_id

    sp = FindLocation(city=city, country=country if country else None)
    if sp is None:
        return flask.make_response(jsonify({'status': 'error', 'message': f"Location '{city}' not found."}), 404)

    location = GCLocation(data={
        'city': sp.m_strCity,
        'country': sp.m_strCountry,
        'latitude': sp.m_fLatitude,
        'longitude': sp.m_fLongitude,
        'tzname': sp.m_strTimeZone
    })

    today = Today()
    if year_param:
        current_year = int(year_param)
        start_date = GCGregorianDate(year=current_year, month=1, day=1)
    else:
        current_year = today.year
        start_date = GCGregorianDate(year=today.year, month=today.month, day=today.day)

    tc = TCalendar()
    tc.CalculateCalendar(location, start_date, 365)

    simp_query = simplify(query_term)
    matched_day = None
    matching_event_text = ""

    for day in tc.days_iter():
        day_dict = dict(day)
        ekadashi_name = day_dict.get('ekadashiName', '')
        if ekadashi_name and simp_query in simplify(ekadashi_name):
            matched_day = day_dict
            matching_event_text = f"{ekadashi_name} Ekadashi"
            break
        
        events = day_dict.get('events', [])
        for ev in events:
            ev_text = ev.get('text', '')
            if simp_query in simplify(ev_text):
                matched_day = day_dict
                matching_event_text = ev_text
                break
        if matched_day:
            break

    if not matched_day:
        return jsonify({
            'status': 'success',
            'data': {
                'event_id': event_id,
                'provider': 'vaisnava_calendar',
                'is_event_eligible': False,
                'location': {'city': city, 'country': country},
                'occurrence': None
            }
        })

    date_obj = matched_day.get('date', {})
    gregorian_str = f"{date_obj.get('year', current_year):04d}-{date_obj.get('month', 1):02d}-{date_obj.get('day', 1):02d}"
    astro = matched_day.get('astrodata', {})

    fast_notes = matched_day.get('fast_notes', '')
    fast_type = matched_day.get('fast_type', 'NO_FAST')
    is_fasting = bool(matched_day.get('fast', 0) or fast_notes)

    for ev in matched_day.get('events', []):
        ev_text = ev.get('text', '')
        if 'fasttype' in ev and ev['fasttype'] > 0:
            ft = ev['fasttype']
            if ft == 1:
                fast_type = 'FAST_TIL_NOON'
                if not fast_notes: fast_notes = 'Fast till noon'
            elif ft == 2:
                fast_type = 'FAST_TIL_SUNSET'
                if not fast_notes: fast_notes = 'Fast till sunset'
            elif ft == 3:
                fast_type = 'FAST_TIL_MOONRISE'
                if not fast_notes: fast_notes = 'Fast till moonrise'
            elif ft == 4:
                fast_type = 'FAST_TIL_MIDNIGHT'
                if not fast_notes: fast_notes = 'Fast till midnight'
            elif ft >= 5:
                fast_type = 'FAST_TIL_NEXT_DAY'
                if not fast_notes: fast_notes = 'Fast till next day'
            is_fasting = True

        if ev_text.startswith('(Fast') or (('fast' in ev_text.lower()) and not fast_notes):
            fast_notes = ev_text.strip('()')
            is_fasting = True
            if 'noon' in ev_text.lower(): fast_type = 'FAST_TIL_NOON'
            elif 'midnight' in ev_text.lower(): fast_type = 'FAST_TIL_MIDNIGHT'
            elif 'sunset' in ev_text.lower(): fast_type = 'FAST_TIL_SUNSET'

    occurrence = {
        'gregorian_date': gregorian_str,
        'date': date_obj,
        'matching_event': matching_event_text or query_term,
        'tithi': astro.get('tithiName', ''),
        'masa': astro.get('masaName', ''),
        'gaurabda_year': astro.get('gaurabdaYear', 540),
        'fasting': {
            'is_fasting_day': is_fasting,
            'fast_type': fast_type,
            'fast_notes': fast_notes
        }
    }


    return jsonify({
        'status': 'success',
        'data': {
            'event_id': event_id,
            'provider': 'vaisnava_calendar',
            'location': {
                'city': location.m_strCity,
                'country': location.m_strCountry,
                'latitude': location.m_fLatitude,
                'longitude': location.m_fLongitude,
                'tzname': location.m_strTimeZone
            },
            'occurrence': occurrence,
            'is_event_eligible': True
        }
    })

def run_server(port=8047, host="127.0.0.1"):
    app.run(host=host, port=port)

if __name__=='__main__':
    run_server()