import streamlit as st
import pandas as pd
from logic import *
import folium
from streamlit_folium import st_folium
from shapely import wkt
from shapely.geometry import GeometryCollection

st.set_page_config(page_title="Railway journey planner 🚂", layout="wide")

# Sidebar Page Navigation

page = st.sidebar.radio("Select a page", ("Journey Planner", "Page 2"))

# Page 1: Railway Journey Planner
if page == "Journey Planner":
    st.title("Railway journey planner 🚂")

    if "selected_points" not in st.session_state:
        st.session_state.selected_points = []

    if "lines" not in st.session_state:
        st.session_state.lines = []

    if "endpoints" not in st.session_state:
        st.session_state.endpoints = []

    if "ready" not in st.session_state:
        st.session_state.ready = False

    if "routes" not in st.session_state:
        st.session_state.routes = None

    if "route_with_change" not in st.session_state:
        st.session_state.route_with_change = None

    if "filtered_routes" not in st.session_state:
        st.session_state.filtered_routes = None

    if "no_results" not in st.session_state:
        st.session_state.no_results = False

    if "alternative_lines" not in st.session_state:
        st.session_state.alternative_lines = []

    # Sidebar for Filtering and Point Selection
    if st.session_state.ready:
        st.sidebar.write("### Filtering")
        st.sidebar.write("#### Maximum walking distance")
        max_walking_distance = st.sidebar.slider("Distance (km)", 0.0, 10.0, 10.0, 0.1)

        st.sidebar.write("#### Stations")
        start_stations = sorted(
            set(route["start_station"] for route in (st.session_state.routes or []))
        )
        end_stations = sorted(
            set(route["end_station"] for route in (st.session_state.routes or []))
        )
        operators = sorted(
            set(
                route["operator"]
                for route in (st.session_state.routes or [])
                if route["operator"]
            )
        )

        start_station_filter = st.sidebar.selectbox(
            "Start station", ["All"] + start_stations
        )
        end_station_filter = st.sidebar.selectbox("End station", ["All"] + end_stations)

        st.sidebar.write("#### Operators")
        selected_operators = []
        for operator in operators:
            if operator:
                if st.sidebar.checkbox(operator, value=True):
                    selected_operators.append(operator)

        other = st.sidebar.checkbox("Other (no operator)", value=True)

        st.sidebar.write("#### Other")
        unique_routes_only = st.sidebar.checkbox(
            "Show only one route per start-end station pair", value=False
        )
        unique_route_names_only = st.sidebar.checkbox(
            "Show only the option with the closest stations for a given route", value=False
        )

        if st.sidebar.button("Filter"):
            if st.session_state.routes is not None:
                filtered_routes = [
                    route
                    for route in st.session_state.routes
                    if (
                        route["total_distance"] <= max_walking_distance
                        and (
                            start_station_filter == "All"
                            or start_station_filter == route["start_station"]
                        )
                        and (
                            end_station_filter == "All"
                            or end_station_filter == route["end_station"]
                        )
                        and (
                            route.get("operator") in selected_operators
                            or (other and not route.get("operator"))
                        )
                    )
                ]

            if unique_routes_only:
                filtered_routes = get_unique_routes(filtered_routes)
            if unique_route_names_only:
                filtered_routes = get_unique_routes_by_name(filtered_routes)

            if not filtered_routes:
                st.session_state.no_results = True
            else:
                st.session_state.no_results = False

            st.session_state.filtered_routes = filtered_routes

        if st.sidebar.button("Clear filters"):
            st.session_state.filtered_routes = None
            st.session_state.no_results = False

    # Functionality for selecting points and handling the map
    def handle_map_click(lat_, lon_):
        if len(st.session_state.selected_points) < 2:
            st.session_state.selected_points.append({"lat": lat_, "lon": lon_})
            st.rerun()
        else:
            st.warning("You can only select two points. Clear the points to reset.")

    # Sidebar for adding points manually
    lat = st.sidebar.number_input("Latitude", value=0.0, format="%.6f")
    lon = st.sidebar.number_input("Longitude", value=0.0, format="%.6f")
    if st.sidebar.button("Add Point"):
        handle_map_click(lat, lon)

    if st.session_state.selected_points:
        st.sidebar.write("### Selected points")
        for idx, point in enumerate(st.session_state.selected_points):
            st.sidebar.write(
                f"Point {idx + 1}:\n\n Latitude {round(point['lat'], 3)}, Longitude {round(point['lon'], 3)}"
            )

    if st.sidebar.button("Clear selected points"):
        st.session_state.selected_points = []
        st.session_state.lines = []
        st.session_state.endpoints = []
        st.session_state.ready = False
        st.session_state.routes = None
        st.session_state.no_results = False
        st.session_state.filtered_routes = None
        st.session_state.alternative_lines = []

    m = folium.Map(location=[52.228, 21.0], zoom_start=10)

    for point in st.session_state.selected_points:
        folium.Marker([point["lat"], point["lon"]], tooltip="Selected Point").add_to(m)

    for point in st.session_state.endpoints:
        folium.CircleMarker(
            [point[0], point[1]],
            tooltip=point[2],
            radius=10,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.7,
        ).add_to(m)

    for line_coords in st.session_state.alternative_lines:
        folium.PolyLine(line_coords, color="pink", weight=1).add_to(m)

    for line_coords in st.session_state.lines:
        folium.PolyLine(line_coords, color="red", weight=3).add_to(m)

    if len(st.session_state.selected_points) < 2:
        m.add_child(folium.ClickForMarker(popup=None))

    map_data = st_folium(m, width=1000, height=550)

    if map_data and map_data.get("last_clicked") is not None:
        lat, lon = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
        if {"lat": lat, "lon": lon} not in st.session_state.selected_points:
            handle_map_click(lat, lon)

    if len(st.session_state.selected_points) == 2 and not st.session_state.ready:
        lat1, lon1 = (
            st.session_state.selected_points[0]["lat"],
            st.session_state.selected_points[0]["lon"],
        )
        lat2, lon2 = (
            st.session_state.selected_points[1]["lat"],
            st.session_state.selected_points[1]["lon"],
        )

        try:
            common_routes = find_common_routes(lat1, lon1, lat2, lon2)
            st.session_state.ready = True

            if common_routes:
                closest_route = common_routes[0]
                geometry_wkt = get_route_geometry(closest_route["route"])
                geometry = wkt.loads(geometry_wkt)

                if geometry.geom_type == "GeometryCollection":
                    for geom in geometry.geoms:
                        if geom.geom_type == "LineString":
                            coordinates = [(point[1], point[0]) for point in geom.coords]
                            st.session_state.lines.append(coordinates)

                start_station_geometry = wkt.loads(closest_route["start_station_geometry"])
                end_station_geometry = wkt.loads(closest_route["end_station_geometry"])

                if start_station_geometry.geom_type == "Point":
                    st.session_state.endpoints.append(
                        (
                            start_station_geometry.y,
                            start_station_geometry.x,
                            closest_route["start_station"],
                        )
                    )

                if end_station_geometry.geom_type == "Point":
                    st.session_state.endpoints.append(
                        (
                            end_station_geometry.y,
                            end_station_geometry.x,
                            closest_route["end_station"],
                        )
                    )

                common_routes[0]["details_start"] = get_station_details(
                    closest_route["start_station"]
                )
                common_routes[0]["details_end"] = get_station_details(
                    closest_route["end_station"]
                )

                st.session_state.routes = common_routes
                st.rerun()
            else:
                possible_routes = find_routes_with_change(lat1, lon1, lat2, lon2)
                if possible_routes:
                    st.session_state.route_with_change = possible_routes
                    # (Add logic for possible routes with changes here)
            st.rerun()

        except Exception as e:
            st.error(f"An error occurred: {e}")

# Page 2: Placeholder for other content (for example, statistics or information)
elif page == "Page 2" and len(st.session_state.selected_points) == 2:
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
            data.append(
                [
                    osm_id,
                    location,
                    reference_point,
                    float(distance),
                    lat,
                    lon,
                    amenity,
                    name,
                ]
            )
        return pd.DataFrame(
            data,
            columns=[
                "OSM ID",
                "Location",
                "Reference Point",
                "Distance (km)",
                "Latitude",
                "Longitude",
                "Amenity",
                "Name",
            ],
        )


    st.title("Nearby Amenities Query")

    if len(st.session_state.selected_points) in [0,1]:
        lat, lon = 52.237049, 21.017532
    else:
        lat, lon = st.session_state.selected_points[1]["lat"], st.session_state.selected_points[1]["lon"]

    reference_point = f"POINT({lon} {lat})"
    st.write(f"Using hardcoded location: {reference_point}")

    available_amenities = [
        "hotel",
        "post_box",
        "restaurant",
        "hospital",
        "ice_cream",
        "cafe",
        "taxi",
    ]
    selected_amenities = st.multiselect(
        "Select amenity types to display", available_amenities, default=available_amenities
    )

    distance_filter = st.slider(
        "Select maximum distance (in km) for nearby amenities",
        min_value=0.25,
        max_value=10.0,
        value=2.0,
        step=0.25,
    )
    st.write(f"Filtering amenities within {distance_filter} km.")

    if (
            "query_results" not in st.session_state
            or st.session_state.distance_filter != distance_filter
    ):
        with st.spinner("Querying data..."):
            sparql_results = query_sparql(
                reference_point, selected_amenities, distance_filter
            )
            st.session_state.query_results = sparql_results
            st.session_state.distance_filter = (
                distance_filter  # Store the current distance filter
            )

    if selected_amenities:
        filtered_results = [
            result
            for result in st.session_state.query_results
            if result["amenity"]["value"] in selected_amenities
        ]
        if filtered_results:
            df = process_results(filtered_results)
            st.success("Query successful!")

            color_map = {
                "hotel": "#1f77b4",
                "post_box": "#ff7f0e",
                "restaurant": "#2ca02c",
                "hospital": "#d62728",
                "ice_cream": "#9467bd",
                "cafe": "#8c564b",
                "taxi": "#e377c2",
            }

            m = folium.Map(location=[lat, lon], zoom_start=14)
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
                        popup=(
                            f"<b>Amenity:</b> {row['Amenity']}<br>"
                            f"<b>Name:</b> {row['Name']}<br>"
                            f"<b>OSM ID:</b> {row['OSM ID']}<br>"
                            f"<b>Distance:</b> {row['Distance (km)']} km"
                        ),
                    ).add_to(m)


            st_folium(m, width=1000, height=550)
        else:
            st.warning("No data found for the selected amenities.")
    else:
        st.warning("Please select at least one amenity type to query.")
