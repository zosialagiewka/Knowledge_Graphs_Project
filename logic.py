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
        '''

    def query(self, q):
        self.sparql.setQuery(self.header + q)
        self.sparql.setReturnFormat(JSON)
        result = self.sparql.query().convert()
        result = result["results"]["bindings"]

        return map(lambda x: {k: v["value"] for k, v in x.items()}, result)

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