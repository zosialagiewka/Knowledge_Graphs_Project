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
    query = f"""
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
    """
    results = wikidata_connection.query(query)
    return results