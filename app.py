import streamlit as st
import pandas as pd
from logic import *
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Railway journey planner", layout="wide")

st.title("Railway journey planner")

if "selected_points" not in st.session_state:
    st.session_state.selected_points = []


def handle_map_click(lat, lon):
    if len(st.session_state.selected_points) < 2:
        st.session_state.selected_points.append({"lat": lat, "lon": lon})
        st.rerun()
    else:
        st.warning("You can only select two points. Clear the points to reset.")


c1, c2 = st.columns(2)
with c1:
    st.write("### Add points manually")
    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Latitude", value=0.0, format="%.6f")
        lon = st.number_input("Longitude", value=0.0, format="%.6f")
    if st.button("Add Point"):
        handle_map_click(lat, lon)

    if st.button("Clear selected points"):
        st.session_state.selected_points = []

    if st.session_state.selected_points:
        st.write("### Selected points")
        for idx, point in enumerate(st.session_state.selected_points):
            st.write(f"Point {idx + 1}: Latitude {point['lat']}, Longitude {point['lon']}")

with c2:
    st.write("### Map view")
    m = folium.Map(location=[52.228, 21.0], zoom_start=14)
    for point in st.session_state.selected_points:
        folium.Marker([point['lat'], point['lon']], tooltip="Selected Point").add_to(m)

    if len(st.session_state.selected_points) < 2:
        m.add_child(folium.ClickForMarker(popup=None))

    map_data = st_folium(m, width=700, height=500)

if map_data and map_data.get('last_clicked') is not None:
    lat, lon = map_data['last_clicked']['lat'], map_data['last_clicked']['lng']
    if {"lat": lat, "lon": lon} not in st.session_state.selected_points:
        handle_map_click(lat, lon)

if len(st.session_state.selected_points) == 2:
    lat1, lon1 = st.session_state.selected_points[0]["lat"], st.session_state.selected_points[0]["lon"]
    lat2, lon2 = st.session_state.selected_points[1]["lat"], st.session_state.selected_points[1]["lon"]

    st.write("### Train routes")
    try:
        # train_routes = find_train_route(lat1, lon1, lat2, lon2)
        train_routes = get_routes_between_two_places(lat1, lon1, lat2, lon2)
        if train_routes:
            st.write(train_routes)

            from_station_name = train_routes[0]['from']
            to_station_name = train_routes[0]['to']

            st.write(f"### Station details for {from_station_name}")
            from_station_details = get_station_details(from_station_name)
            if from_station_details:
                st.write(from_station_details)

            st.write(f"### Station details for {to_station_name}")
            to_station_details = get_station_details(to_station_name)
            if to_station_details:
                st.write(to_station_details)
        else:
            st.write("No train routes found between the selected points.")
    except Exception as e:
        st.error(f"An error occurred while fetching train routes: {e}")
else:
    st.info("Please select or add coordinates for two points to find a train route.")
