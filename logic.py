from SPARQLWrapper import SPARQLWrapper, JSON

class SparqlConnection:
    def __init__(self):
        self.ENDPOINT_URL = "https://qlever.cs.uni-freiburg.de/api/osm-planet"
        self.sparql = SPARQLWrapper(self.ENDPOINT_URL)
        self.header = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX geo: <http://www.opengis.net/ont/geosparql#>
            PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
            PREFIX osm: <https://www.openstreetmap.org/>
            PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>
            PREFIX osm2rdfmember: <https://osm2rdf.cs.uni-freiburg.de/rdf/member#>
            PREFIX osmrel: <https://www.openstreetmap.org/relation/>
            PREFIX osmway: <https://www.openstreetmap.org/way/>
            PREFIX ogc: <http://www.opengis.net/rdf#>
        """

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


def find_routes_near_point(longitude, latitude, radius=5):
    query = f"""
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
    """
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
                common_routes_with_stations.append(
                    {
                        "route": route,
                        "route_name": station_a["routeName"],
                        "start_station": station_a["stationName"],
                        "start_station_geometry": station_a["stationGeometry"],
                        "end_station": station_b["stationName"],
                        "end_station_geometry": station_b["stationGeometry"],
                        "total_distance": float(station_a["distance"]) + float(station_b["distance"])
                    }
                )

    return sorted(common_routes_with_stations, key=lambda x: x["total_distance"])


def find_routes_with_change(lat1, lon1, lat2, lon2, radius=5):
    routes_place_a = find_routes_near_point(lon1, lat1, radius)
    routes_place_b = find_routes_near_point(lon2, lat2, radius)

    routes_a_ids = list(route for route in routes_place_a)
    routes_b_ids = list(route for route in routes_place_b)

    possible_routes_with_change = []
    for route_a in routes_a_ids:
        for route_b in routes_b_ids:
            intersections = get_intersections(route_a["route"], route_b["route"])
            if len(intersections) > 0:
                print(route_a)
                print(route_b)
                possible_routes_with_change.append((
                    route_a["route"],
                    route_b["route"],
                    intersections[0]["station1"],
                    route_a["stationName"],
                    route_b["stationName"],
                    route_a["stationGeometry"],
                    route_b["stationGeometry"],
                ))
                if len(possible_routes_with_change) >= 2:
                    return possible_routes_with_change

    return possible_routes_with_change


def get_intersections(route1, route2):
    query = f"""
        SELECT ?station1 ?stationName WHERE {{
            <{route1}> ogc:sfContains ?station1 .
            ?station1 osmkey:name ?stationName .
            
            <{route2}> ogc:sfContains ?station2 .
            ?station2 osmkey:name ?stationName .
            
            ?station1 osmkey:railway "stop" .
        }}
        GROUP BY ?stationName ?station1
        LIMIT 1
    """

    results = connection.query(query)
    return results


def get_route_geometry(route):
    query = f"""
        SELECT ?railGeometry WHERE {{
            <{route}> geo:hasGeometry/geo:asWKT ?railGeometry .
        }}
    """
    results = connection.query(query)

    return results[0]["railGeometry"]
