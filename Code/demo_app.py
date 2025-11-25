def show_dashboard():
    st.markdown("<h1 class='main-header'>System Dashboard</h1>", unsafe_allow_html=True)
    
    # Add custom CSS for dashboard components
    st.markdown("""
    <style>
    .dashboard-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        margin-bottom: 1rem;
    }
    .dashboard-card-dark {
        background-color: #343a40;
        color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.2);
        margin-bottom: 1rem;
    }
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-green {
        background-color: #28a745;
    }
    .status-yellow {
        background-color: #ffc107;
    }
    .status-red {
        background-color: #dc3545;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Dashboard tabs
    tabs = st.tabs(["System Status", "Traffic Metrics", "Performance Analytics", "Alerts & Notifications"])
    
    with tabs[0]:
        st.subheader("System Status Overview")
        
        # System status cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="dashboard-card">
                <h3>Camera Network</h3>
                <p><span class="status-indicator status-green"></span> Online (12/12)</p>
                <p>Last check: 2 minutes ago</p>
                <p>Uptime: 99.8%</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class="dashboard-card">
                <h3>Processing Units</h3>
                <p><span class="status-indicator status-green"></span> Normal Operation</p>
                <p>CPU Usage: 42%</p>
                <p>Memory: 3.2/8 GB</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
            <div class="dashboard-card">
                <h3>Signal Controllers</h3>
                <p><span class="status-indicator status-green"></span> All Operational</p>
                <p>Connected: 4/4</p>
                <p>Response time: 120ms</p>
            </div>
            """, unsafe_allow_html=True)
        
        # System health metrics
        st.subheader("System Health")
        col1, col2 = st.columns(2)
        
        with col1:
            # Mock CPU usage over time
            cpu_data = pd.DataFrame({
                'Time': pd.date_range(start='2023-01-01', periods=24, freq='H'),
                'CPU Usage (%)': 30 + 15 * np.sin(np.linspace(0, 4*np.pi, 24)) + np.random.normal(0, 3, 24)
            })
            
            cpu_chart = alt.Chart(cpu_data).mark_line().encode(
                x=alt.X('Time:T', title='Time'),
                y=alt.Y('CPU Usage (%):Q', scale=alt.Scale(domain=[0, 100])),
                tooltip=['Time:T', 'CPU Usage (%):Q']
            ).properties(
                title='CPU Usage Over Time',
                width=400,
                height=200
            )
            
            st.altair_chart(cpu_chart, use_container_width=True)
        
        with col2:
            # Mock memory usage over time
            memory_data = pd.DataFrame({
                'Time': pd.date_range(start='2023-01-01', periods=24, freq='H'),
                'Memory Usage (GB)': 2 + 1.2 * np.sin(np.linspace(0, 2*np.pi, 24)) + np.random.normal(0, 0.2, 24)
            })
            
            memory_chart = alt.Chart(memory_data).mark_area(
                line={'color':'#1E88E5'},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='white', offset=0),
                           alt.GradientStop(color='#1E88E5', offset=1)],
                    x1=1,
                    x2=1,
                    y1=1,
                    y2=0
                )
            ).encode(
                x=alt.X('Time:T', title='Time'),
                y=alt.Y('Memory Usage (GB):Q', scale=alt.Scale(domain=[0, 8])),
                tooltip=['Time:T', 'Memory Usage (GB):Q']
            ).properties(
                title='Memory Usage Over Time',
                width=400,
                height=200
            )
            
            st.altair_chart(memory_chart, use_container_width=True)
        
        # Network status
        st.subheader("Network Status")
        
        # Mock network data
        network_data = {
            'Interface': ['Camera Network', 'Control Network', 'Cloud Uplink', 'Maintenance Link'],
            'Status': ['Online', 'Online', 'Online', 'Online'],
            'Bandwidth (Mbps)': [95.2, 42.8, 18.5, 5.2],
            'Latency (ms)': [12, 8, 45, 22],
            'Packet Loss (%)': [0.02, 0.00, 0.15, 0.05]
        }
        
        network_df = pd.DataFrame(network_data)
        
        # Add color coding based on status
        def color_status(val):
            if val == 'Online':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'Degraded':
                return 'background-color: #fff3cd; color: #856404'
            else:
                return 'background-color: #f8d7da; color: #721c24'
        
        st.dataframe(network_df.style.applymap(color_status, subset=['Status']), use_container_width=True)
    
    with tabs[1]:
        st.subheader("Real-time Traffic Metrics")
        
        # Traffic volume metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Current Traffic Volume", value="342 vehicles/hour", delta="12%")
        
        with col2:
            st.metric(label="Average Wait Time", value="45 seconds", delta="-18%")
        
        with col3:
            st.metric(label="Intersection Efficiency", value="87%", delta="5%")
        
        # Traffic volume by intersection
        st.subheader("Traffic Volume by Intersection")
        
        # Mock intersection data
        intersections = ['Main St & 5th Ave', 'Broadway & Park Rd', 'Central Ave & Oak St', 'Highland & River Rd']
        current_volume = [342, 285, 198, 156]
        capacity = [400, 350, 300, 250]
        
        # Create a DataFrame for the chart
        intersection_data = pd.DataFrame({
            'Intersection': intersections,
            'Current Volume': current_volume,
            'Capacity': capacity
        })
        
        # Calculate utilization percentage
        intersection_data['Utilization (%)'] = (intersection_data['Current Volume'] / intersection_data['Capacity'] * 100).round(1)
        
        # Create a horizontal bar chart
        volume_chart = alt.Chart(intersection_data).mark_bar().encode(
            y=alt.Y('Intersection:N', sort='-x'),
            x=alt.X('Current Volume:Q', title='Vehicles per Hour'),
            color=alt.condition(
                alt.datum['Utilization (%)'] > 80,
                alt.value('#dc3545'),  # red for high utilization
                alt.condition(
                    alt.datum['Utilization (%)'] > 60,
                    alt.value('#ffc107'),  # yellow for medium utilization
                    alt.value('#28a745')  # green for low utilization
                )
            ),
            tooltip=['Intersection:N', 'Current Volume:Q', 'Capacity:Q', 'Utilization (%):Q']
        ).properties(
            title='Current Traffic Volume by Intersection',
            height=200
        )
        
        # Add capacity reference lines
        capacity_lines = alt.Chart(intersection_data).mark_rule(
            color='red',
            strokeDash=[5, 5]
        ).encode(
            y='Intersection:N',
            x='Capacity:Q'
        )
        
        # Combine the charts
        combined_chart = volume_chart + capacity_lines
        
        st.altair_chart(combined_chart, use_container_width=True)
        
        # Traffic patterns over time
        st.subheader("Traffic Patterns (24-hour)")
        
        # Generate mock hourly data
        hours = list(range(24))
        
        # Create different traffic patterns for each intersection
        traffic_data = pd.DataFrame({
            'Hour': hours * len(intersections),
            'Intersection': sum([[intersection] * 24 for intersection in intersections], []),
            'Volume': np.concatenate([
                150 + 100 * np.sin((np.array(hours) - 8) * np.pi / 12) + np.random.normal(0, 10, 24),  # Main St pattern
                120 + 80 * np.sin((np.array(hours) - 9) * np.pi / 12) + np.random.normal(0, 8, 24),    # Broadway pattern
                100 + 60 * np.sin((np.array(hours) - 7) * np.pi / 12) + np.random.normal(0, 6, 24),    # Central Ave pattern
                80 + 40 * np.sin((np.array(hours) - 10) * np.pi / 12) + np.random.normal(0, 5, 24)     # Highland pattern
            ])
        })
        
        # Create a line chart for traffic patterns
        pattern_chart = alt.Chart(traffic_data).mark_line().encode(
            x=alt.X('Hour:Q', title='Hour of Day', scale=alt.Scale(domain=[0, 23])),
            y=alt.Y('Volume:Q', title='Vehicles per Hour'),
            color=alt.Color('Intersection:N', legend=alt.Legend(title="Intersection")),
            tooltip=['Hour:Q', 'Volume:Q', 'Intersection:N']
        ).properties(
            title='24-hour Traffic Volume by Intersection',
            height=300
        )
        
        st.altair_chart(pattern_chart, use_container_width=True)
    
    with tabs[2]:
        st.subheader("Performance Analytics")
        
        # Time period selector
        time_period = st.selectbox(
            "Select Time Period",
            ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Last Quarter", "Last Year"]
        )
        
        # Key performance indicators
        st.subheader("Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(label="Avg. Wait Time Reduction", value="42%", delta="8%")
        
        with col2:
            st.metric(label="Fuel Savings", value="12,450 gal", delta="5%")
        
        with col3:
            st.metric(label="CO₂ Reduction", value="124 tons", delta="7%")
        
        with col4:
            st.metric(label="System Accuracy", value="94.2%", delta="1.5%")
        
        # Performance comparison
        st.subheader("Before vs. After Implementation")
        
        # Mock comparison data
        metrics = ['Average Wait Time (sec)', 'Traffic Flow Rate (veh/min)', 'Congestion Duration (min/day)', 'Fuel Consumption (gal/day)']
        before = [78, 12, 124, 1450]
        after = [45, 18, 52, 1120]
        
        # Create a DataFrame for the chart
        comparison_data = pd.DataFrame({
            'Metric': metrics + metrics,
            'Value': before + after,
            'System': ['Before'] * len(metrics) + ['After'] * len(metrics)
        })
        
        # Create a grouped bar chart
        comparison_chart = alt.Chart(comparison_data).mark_bar().encode(
            x=alt.X('System:N', title=None),
            y=alt.Y('Value:Q', title='Value'),
            color=alt.Color('System:N', scale=alt.Scale(
                domain=['Before', 'After'],
                range=['#dc3545', '#28a745']
            )),
            column=alt.Column('Metric:N', title=None),
            tooltip=['Metric:N', 'Value:Q', 'System:N']
        ).properties(
            width=100,
            height=250
        )
        
        st.altair_chart(comparison_chart, use_container_width=True)
        
        # System efficiency over time
        st.subheader("System Efficiency Over Time")
        
        # Generate mock efficiency data
        dates = pd.date_range(start='2023-01-01', periods=90, freq='D')
        
        # Create efficiency trend with gradual improvement
        base_efficiency = 75
        improvement = np.minimum(15 * (1 - np.exp(-np.arange(90) / 30)), 15)
        noise = np.random.normal(0, 1.5, 90)
        efficiency = base_efficiency + improvement + noise
        
        # Create a DataFrame for the chart
        efficiency_data = pd.DataFrame({
            'Date': dates,
            'Efficiency (%)': efficiency
        })
        
        # Create a line chart with a trend line
        efficiency_chart = alt.Chart(efficiency_data).mark_line(point=True).encode(
            x=alt.X('Date:T', title='Date'),
            y=alt.Y('Efficiency (%):Q', scale=alt.Scale(domain=[70, 100])),
            tooltip=['Date:T', 'Efficiency (%):Q']
        ).properties(
            title='System Efficiency Trend',
            height=300
        )
        
        # Add a trend line
        trend_line = alt.Chart(efficiency_data).transform_regression(
            'Date', 'Efficiency (%)'
        ).mark_line(
            color='red',
            size=3
        ).encode(
            x='Date:T',
            y='Efficiency (%):Q'
        )
        
        # Combine the charts
        combined_efficiency_chart = efficiency_chart + trend_line
        
        st.altair_chart(combined_efficiency_chart, use_container_width=True)
    
    with tabs[3]:
        st.subheader("Alerts & Notifications")
        
        # Alert filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            alert_type = st.multiselect(
                "Alert Type",
                ["System", "Traffic", "Maintenance", "Security"],
                default=["System", "Traffic", "Maintenance"]
            )
        
        with col2:
            severity = st.multiselect(
                "Severity",
                ["Critical", "High", "Medium", "Low"],
                default=["Critical", "High", "Medium"]
            )
        
        with col3:
            time_range = st.selectbox(
                "Time Range",
                ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All"]
            )
        
        # Mock alert data
        alert_data = [
            {"timestamp": "2023-06-15 08:32:14", "type": "Traffic", "severity": "High", "message": "Unusual congestion detected at Main St & 5th Ave", "status": "Active"},
            {"timestamp": "2023-06-15 07:45:22", "type": "System", "severity": "Medium", "message": "Camera #3 at Broadway & Park Rd experiencing intermittent connectivity", "status": "Active"},
            {"timestamp": "2023-06-14 23:12:05", "type": "Maintenance", "severity": "Low", "message": "Scheduled system update completed successfully", "status": "Resolved"},
            {"timestamp": "2023-06-14 17:30:41", "type": "Security", "severity": "Critical", "message": "Unauthorized access attempt detected", "status": "Resolved"},
            {"timestamp": "2023-06-14 14:22:18", "type": "Traffic", "severity": "Medium", "message": "Traffic signal timing adjusted at Central Ave & Oak St due to construction", "status": "Active"},
            {"timestamp": "2023-06-14 10:05:37", "type": "System", "severity": "High", "message": "Processing unit #2 CPU usage exceeded 90% for >5 minutes", "status": "Resolved"},
            {"timestamp": "2023-06-13 19:48:52", "type": "Maintenance", "severity": "Medium", "message": "Battery backup system switched to main power", "status": "Resolved"},
            {"timestamp": "2023-06-13 12:33:09", "type": "Traffic", "severity": "Critical", "message": "Emergency vehicle priority activated at Highland & River Rd", "status": "Resolved"}
        ]
        
        # Convert to DataFrame
        alerts_df = pd.DataFrame(alert_data)
        
        # Apply filters
        filtered_alerts = alerts_df[
            alerts_df["type"].isin(alert_type) &
            alerts_df["severity"].isin(severity)
        ]
        
        # Display alerts with custom styling
        st.markdown("### Recent Alerts")
        
        if len(filtered_alerts) > 0:
            for _, alert in filtered_alerts.iterrows():
                # Set color based on severity
                if alert["severity"] == "Critical":
                    severity_color = "#dc3545"  # red
                elif alert["severity"] == "High":
                    severity_color = "#fd7e14"  # orange
                elif alert["severity"] == "Medium":
                    severity_color = "#ffc107"  # yellow
                else:
                    severity_color = "#6c757d"  # gray
                
                # Set icon based on type
                if alert["type"] == "Traffic":
                    icon = "🚦"
                elif alert["type"] == "System":
                    icon = "💻"
                elif alert["type"] == "Maintenance":
                    icon = "🔧"
                else:
                    icon = "🔒"
                
                # Set status badge
                if alert["status"] == "Active":
                    status_badge = f'<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 10px; font-size: 12px;">Active</span>'
                else:
                    status_badge = f'<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 10px; font-size: 12px;">Resolved</span>'
                
                # Display alert card
                st.markdown(f"""
                <div style="border-left: 5px solid {severity_color}; padding: 10px; margin-bottom: 10px; background-color: #f8f9fa; border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: bold;">{icon} {alert["type"]} Alert - {alert["severity"]}</span>
                        <span>{status_badge}</span>
                    </div>
                    <p style="margin: 5px 0;">{alert["message"]}</p>
                    <p style="color: #6c757d; font-size: 12px; margin: 0;">{alert["timestamp"]}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No alerts match the selected filters.")
        
        # Notification settings
        st.subheader("Notification Settings")
        
        with st.expander("Configure Notification Preferences"):
            st.checkbox("Email Notifications", value=True)
            st.checkbox("SMS Notifications", value=False)
            st.checkbox("Push Notifications", value=True)
            st.checkbox("Daily Summary Report", value=True)
            
            st.selectbox("Minimum Alert Severity for Notifications", ["Critical", "High", "Medium", "Low"], index=1)
            
            st.multiselect(
                "Notification Categories",
                ["System Alerts", "Traffic Incidents", "Maintenance Alerts", "Security Alerts", "Performance Reports"],
                default=["System Alerts", "Traffic Incidents", "Security Alerts"]
            )
            
            if st.button("Save Notification Preferences"):
                st.success("Notification preferences saved successfully!")
    
    # System actions section
    st.markdown("---")
    st.subheader("System Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Run System Diagnostics"):
            with st.spinner("Running diagnostics..."):
                time.sleep(2)
                st.success("Diagnostics completed. All systems operational.")
    
    with col2:
        if st.button("Recalibrate Cameras"):
            with st.spinner("Recalibrating cameras..."):
                time.sleep(2)
                st.success("Camera calibration complete.")
    
    with col3:
        if st.button("Update AI Models"):
            with st.spinner("Updating AI models..."):
                time.sleep(2)
                st.success("AI models updated to latest version.")
    
    with col4:
        if st.button("Generate System Report"):
            with st.spinner("Generating report..."):
                time.sleep(2)
                st.success("Report generated and saved to reports directory.")