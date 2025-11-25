import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt
import time
import cv2
from PIL import Image

# Import the dashboard function from demo_app.py
from Code.demo_app import show_dashboard

# Set page configuration
st.set_page_config(
    page_title="Adaptive Traffic Signal Timer",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1E88E5;
    text-align: center;
    margin-bottom: 1rem;
}
.subheader {
    font-size: 1.5rem;
    color: #333;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Dashboard", "Simulation", "Settings"])

if page == "Home":
    st.markdown("<h1 class='main-header'>Adaptive Traffic Signal Timer</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## About the System
        
        The Adaptive Traffic Signal Timer is an intelligent traffic management system that uses computer vision 
        to detect vehicles and optimize traffic signal timing in real-time.
        
        ### Key Features:
        - Real-time vehicle detection using YOLO
        - Dynamic signal timing based on traffic density
        - Traffic flow optimization algorithms
        - Comprehensive monitoring dashboard
        - Historical data analysis
        """)
        
        st.markdown("### How It Works")
        st.markdown("""
        1. **Vehicle Detection**: Cameras capture video feeds from intersections
        2. **Traffic Analysis**: AI algorithms detect and count vehicles in each lane
        3. **Signal Optimization**: The system calculates optimal signal timing
        4. **Dynamic Control**: Traffic signals adjust in real-time based on current conditions
        """)
    
    with col2:
        try:
            image = Image.open("traffic-signal.jpg")
            st.image(image, caption="Adaptive Traffic Signal System")
        except:
            st.info("Image not found. Please ensure 'traffic-signal.jpg' is in the project root directory.")
        
        st.markdown("### System Status")
        st.success("System is operational")
        
elif page == "Dashboard":
    # Call the dashboard function from demo_app.py
    show_dashboard()
    
elif page == "Simulation":
    st.markdown("<h1 class='main-header'>Traffic Simulation</h1>", unsafe_allow_html=True)
    
    st.info("The simulation module allows you to test the adaptive signal timing algorithm under various traffic conditions.")
    
    st.subheader("Simulation Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        traffic_density = st.slider("Traffic Density", 0.1, 1.0, 0.5, 0.1)
        simulation_speed = st.slider("Simulation Speed", 1, 10, 5, 1)
        
    with col2:
        intersection_type = st.selectbox("Intersection Type", ["4-way", "3-way", "Complex"])
        time_of_day = st.selectbox("Time of Day", ["Morning Rush", "Midday", "Evening Rush", "Night"])
    
    if st.button("Start Simulation"):
        with st.spinner("Running simulation..."):
            time.sleep(2)
            st.success("Simulation started! View the results in the dashboard.")
            
elif page == "Settings":
    st.markdown("<h1 class='main-header'>System Settings</h1>", unsafe_allow_html=True)
    
    st.subheader("Camera Configuration")
    camera_enabled = st.checkbox("Enable Cameras", value=True)
    camera_resolution = st.selectbox("Camera Resolution", ["720p", "1080p", "1440p", "4K"])
    
    st.subheader("Detection Settings")
    detection_threshold = st.slider("Detection Confidence Threshold", 0.0, 1.0, 0.5, 0.05)
    detection_frequency = st.slider("Detection Frequency (fps)", 1, 30, 15, 1)
    
    st.subheader("Signal Control Parameters")
    min_green_time = st.number_input("Minimum Green Time (seconds)", 5, 60, 15, 5)
    max_green_time = st.number_input("Maximum Green Time (seconds)", 30, 180, 90, 10)
    
    if st.button("Save Settings"):
        with st.spinner("Saving settings..."):
            time.sleep(1)
            st.success("Settings saved successfully!")

# Footer
st.markdown("---")
st.markdown("© 2023 Adaptive Traffic Signal Timer | Developed by AI Team")