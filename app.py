import streamlit as st
import pandas as pd
from logic import *

st.set_page_config(page_title="Railway journey planner", layout="wide")

st.title("Railway journey planner")

if "selected_points" not in st.session_state:
    st.session_state.selected_points = []

def handle_map_click(lat, lon):
    if len(st.session_state.selected_points) < 2:
        st.session_state.selected_points.append({"lat": lat, "lon": lon})
    else:
        st.warning("You can only select two points. Clear the points to reset.")

if st.button("Clear Selected Points"):
    st.session_state.selected_points = []

st.write("### Add Points Manually")
col1, col2 = st.columns(2)

with col1:
    lat = st.number_input("Latitude", value=0.0, format="%.6f")
    lon = st.number_input("Longitude", value=0.0, format="%.6f")
if st.button("Add Point"):
    handle_map_click(lat, lon)

if st.session_state.selected_points:
    st.write("### Selected Points")
    for idx, point in enumerate(st.session_state.selected_points):
        st.write(f"Point {idx + 1}: Latitude {point['lat']}, Longitude {point['lon']}")

st.write("### Map View")
map_data = pd.DataFrame(st.session_state.selected_points) if st.session_state.selected_points else pd.DataFrame([], columns=["lat", "lon"])
st.map(map_data, zoom=3)

if len(st.session_state.selected_points) == 2:
    lat1, lon1 = st.session_state.selected_points[0]["lat"], st.session_state.selected_points[0]["lon"]
    lat2, lon2 = st.session_state.selected_points[1]["lat"], st.session_state.selected_points[1]["lon"]

    st.write("### Train Routes")
    try:
        # train_routes = find_train_route(lat1, lon1, lat2, lon2)
        train_routes = find_closest_stations(lat1, lon1)
        if train_routes:
            st.write(train_routes)
        else:
            st.write("No train routes found between the selected points.")
    except Exception as e:
        st.error(f"An error occurred while fetching train routes: {e}")
else:
    st.info("Please select or add coordinates for two points to find a train route.")
