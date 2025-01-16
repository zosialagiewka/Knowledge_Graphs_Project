import streamlit as st
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
from streamlit_folium import st_folium
import folium


def query_sparql(reference_point, selected_amenities, distance_filter):
    sparql = SPARQLWrapper("https://qlever.cs.uni-freiburg.de/api/osm-planet")
    amenities = " ".join(f'"{amenity}"' for amenity in selected_amenities)
    query = f"""
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
    PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>
    PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
    PREFIX osm: <https://www.openstreetmap.org/wiki/>
    SELECT ?osm_id ?location ?referencePoint ?distance ?amenity ?name
    WHERE {{
      BIND("{reference_point}"^^geo:wktLiteral AS ?referencePoint)
      ?osm_id osmkey:amenity ?amenity .
      VALUES ?amenity {{ {amenities} }}
      ?osm_id geo:hasGeometry/geo:asWKT ?location .
      OPTIONAL {{ ?osm_id osmkey:name ?name }}
      BIND(geof:distance(?referencePoint, ?location) AS ?distance)
      FILTER(?distance <= {distance_filter})
    }}
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        return results["results"]["bindings"]
    except Exception as e:
        st.error(f"Error querying SPARQL endpoint: {e}")
        return []


def process_results(sparql_results):
    data = []
    for result in sparql_results:
        osm_id = result.get("osm_id", {}).get("value", "")
        location = result.get("location", {}).get("value", "")
        reference_point = result.get("referencePoint", {}).get("value", "")
        distance = result.get("distance", {}).get("value", "")
        amenity = result.get("amenity", {}).get("value", "")
        name = result.get("name", {}).get("value", "Unknown")
        if location.startswith("POINT"):
            coords = location.strip("POINT()").split()
            lon, lat = float(coords[0]), float(coords[1])
        else:
            lon, lat = None, None
        data.append([osm_id, location, reference_point, float(distance), lat, lon, amenity, name])
    return pd.DataFrame(data,
                        columns=["OSM ID", "Location", "Reference Point", "Distance (km)", "Latitude", "Longitude",
                                 "Amenity", "Name"])


st.title("Nearby Amenities Query")

reference_point = "POINT(21.017532 52.237049)"
st.write(f"Using hardcoded location: {reference_point}")

available_amenities = ["hotel", "post_box", "restaurant", "hospital", "ice_cream", "cafe", "taxi"]
selected_amenities = st.multiselect("Select amenity types to display", available_amenities, default=available_amenities)


distance_filter = st.slider(
    "Select maximum distance (in km) for nearby amenities",
    min_value=0.25,
    max_value=10.0,
    value=2.0,
    step=0.25
)
st.write(f"Filtering amenities within {distance_filter} km.")

if "query_results" not in st.session_state or st.session_state.distance_filter != distance_filter:
    with st.spinner("Querying data..."):
        sparql_results = query_sparql(reference_point, selected_amenities, distance_filter)
        st.session_state.query_results = sparql_results
        st.session_state.distance_filter = distance_filter  # Store the current distance filter

if selected_amenities:
    filtered_results = [result for result in st.session_state.query_results if
                        result['amenity']['value'] in selected_amenities]
    if filtered_results:
        df = process_results(filtered_results)
        st.success("Query successful!")
        st.dataframe(df)

        color_map = {
            "hotel": "#1f77b4",
            "post_box": "#ff7f0e",
            "restaurant": "#2ca02c",
            "hospital": "#d62728",
            "ice_cream": "#9467bd",
            "cafe": "#8c564b",
            "taxi": "#e377c2",
        }

        m = folium.Map(location=[52.237049, 21.017532], zoom_start=14)
        for _, row in df.iterrows():
            if not pd.isna(row["Latitude"]) and not pd.isna(row["Longitude"]):
                color = color_map.get(row["Amenity"], "black")
                folium.CircleMarker(
                    location=[row["Latitude"], row["Longitude"]],
                    radius=6,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    popup=(f"<b>Amenity:</b> {row['Amenity']}<br>"
                           f"<b>Name:</b> {row['Name']}<br>"
                           f"<b>OSM ID:</b> {row['OSM ID']}<br>"
                           f"<b>Distance:</b> {row['Distance (km)']} km"),
                ).add_to(m)

        st_folium(m, width=700, height=500)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name="sparql_query_results.csv",
            mime="text/csv",
        )
    else:
        st.warning("No data found for the selected amenities.")
else:
    st.warning("Please select at least one amenity type to query.")
