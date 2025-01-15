from SPARQLWrapper import SPARQLWrapper, JSON

class SparqlConnection:
    def __init__(self):
        self.ENDPOINT_URL = "https://qlever.cs.uni-freiburg.de/api/osm-planet"
        self.sparql = SPARQLWrapper(self.ENDPOINT_URL)
        self.header = '''
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX geo: <http://www.opengis.net/ont/geosparql#>
            PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
            PREFIX osm: <https://www.openstreetmap.org/>
            PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>
            PREFIX osm2rdfmember: <https://osm2rdf.cs.uni-freiburg.de/rdf/member#>
            PREFIX osmrel: <https://www.openstreetmap.org/relation/>
            PREFIX osmway: <https://www.openstreetmap.org/way/>
            PREFIX ogc: <http://www.opengis.net/rdf#>     
        '''

    def query(self, q):
        self.sparql.setQuery(self.header + q)
        self.sparql.setReturnFormat(JSON)
        result = self.sparql.query().convert()
        result = result["results"]["bindings"]
        result = list(map(lambda x: {k: v["value"] for k, v in x.items()}, result))
        return result


class WikidataConnection:
    def __init__(self):
        self.ENDPOINT_URL = "https://query.wikidata.org/sparql"
        self.sparql = SPARQLWrapper(self.ENDPOINT_URL)

    def query(self, q):
        self.sparql.setQuery(q)
        self.sparql.setReturnFormat(JSON)
        result = self.sparql.query().convert()
        result = result["results"]["bindings"]
        result = [{k: v.get("value", "") for k, v in item.items()} for item in result]
        return result


wikidata_connection = WikidataConnection()

connection = SparqlConnection()


def find_closest_stations(longitude, latitude):
    query = f'''
        SELECT ?station ?stationGeometry ?name ?distance WHERE {{
            BIND("POINT({latitude} {longitude})"^^geo:wktLiteral AS ?referencePoint)
            
            ?station rdf:type osm:node ;
                    osmkey:railway "station" ;
                    osmkey:train "yes" ;
                    osmkey:name ?name ;
                    geo:hasGeometry/geo:asWKT ?stationGeometry .
                    
            BIND(geof:distance(?referencePoint, ?stationGeometry) AS ?distance)
            FILTER(?distance <= 5)
        }}
        ORDER BY ?distance
    '''

    # "station", "stationGeometry", "name", "distance"
    results = connection.query(query)
    return results


def find_train_route(lon1, lat1, lon2, lat2):
    from_station = find_closest_stations(lon1, lat1)[0]
    to_station = find_closest_stations(lon2, lat2)[0]

    query = f"""
        SELECT ?route ?from ?to WHERE {{
        ?route osmkey:route "train" ;
            osmkey:from {from_station["name"]} ;
            osmkey:to {to_station["name"]} .  
        }}
        LIMIT 1
    """

    results = connection.query(query)
    return results


def get_routes_between_two_places(lon1, lat1, lon2, lat2):
    query = f"""
        SELECT ?route ?from ?to WHERE {{
            ?route osmkey:route "train" ;
                   osmkey:from ?from ;
                   osmkey:to ?to ;
                   geo:hasGeometry/geo:asWKT ?location .
    
            FILTER (regex(?location, "{lat1:.2f}[0-9]* {lon1:.2f}[0-9]*"))
            FILTER (regex(?location, "{lat2:.2f}[0-9]* {lon2:.2f}[0-9]*"))
    }}
        LIMIT 10
    """
    results = connection.query(query)
    return results


def get_station_details(station_name):
    query = f'''
        SELECT DISTINCT ?station ?street_address ?coordinate_location ?adjacent_station ?official_website ?date_of_official_opening
        WHERE {{
          ?station rdfs:label ?stationLabel;
            wdt:P31 wd:Q55488.
          FILTER (CONTAINS(LCASE(?stationLabel), LCASE("{station_name}")))
          OPTIONAL {{ ?station wdt:P6375 ?street_address. }}
          OPTIONAL {{ ?station wdt:P625 ?coordinate_location. }}
          OPTIONAL {{ ?station wdt:P856 ?official_website. }}
          OPTIONAL {{ ?station wdt:P1619 ?date_of_official_opening. }}
        }}
        LIMIT 50
    '''
    results = wikidata_connection.query(query)
    return results


####################################


def find_routes_near_point(longitude, latitude, radius=5):
    query = f'''
        SELECT ?route ?routeName ?stationGeometry ?stationName ?distance WHERE {{
            BIND ("POINT({longitude} {latitude})"^^geo:wktLiteral AS ?referencePoint)

            ?station osmkey:railway "stop" ;
                     osmkey:name ?stationName ;
                     geo:hasGeometry/geo:asWKT ?stationGeometry .
            BIND (geof:distance(?referencePoint, ?stationGeometry) AS ?distance)
            FILTER (?distance <= {radius})

            ?route ogc:sfContains ?station ;
                   osmkey:route ?routeType ;
                   osmkey:name ?routeName ;
            FILTER (?routeType IN ("train", "railway"))
        }}
        ORDER BY ?distance
    '''
    results = connection.query(query)

    return results


def find_common_routes(lat1, lon1, lat2, lon2, radius=5):
    routes_place_a = find_routes_near_point(lon1, lat1, radius)
    routes_place_b = find_routes_near_point(lon2, lat2, radius)

    routes_a_ids = set(route["route"] for route in routes_place_a)
    routes_b_ids = set(route["route"] for route in routes_place_b)

    common_routes = routes_a_ids & routes_b_ids

    common_routes_with_stations = []
    for route in common_routes:
        stations_a = [r for r in routes_place_a if r["route"] == route]
        stations_b = [r for r in routes_place_b if r["route"] == route]
        for station_a in stations_a:
            for station_b in stations_b:
                total_distance = float(station_a["distance"]) + float(station_b["distance"])
                common_routes_with_stations.append({
                    "route": route,
                    "route_name": station_a["routeName"],
                    "start_station": station_a["stationName"],
                    "end_station": station_b["stationName"],
                    "total_distance": total_distance
                })

    return sorted(common_routes_with_stations, key=lambda x: x["total_distance"])

