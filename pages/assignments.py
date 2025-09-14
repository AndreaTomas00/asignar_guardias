import streamlit as st
import pandas as pd
import altair as alt
import os
from utils.calendar_utils import get_shifts_data, get_shift_color, draw_assignment_calendar

def show_assignments(selected_month, year, month_names):
    """Display shift assignments"""
    st.header("Shift Assignments")
    
    try:
        # Get the month number from the month name
        selected_month_num = month_names.index(selected_month) + 1
        
        # Look for the most recent assignment file
        assignment_files = [f for f in os.listdir(".") if f.startswith("assignments_") and f.endswith(".csv")]
        
        if not assignment_files:
            # Check parent directory
            parent_files = [f for f in os.listdir("..") if f.startswith("shift_assignments") and f.endswith(".csv")]
            if parent_files:
                assignments_file = os.path.join("..", parent_files[0])
            else:
                st.error("No assignment files found.")
                return
        else:
            assignments_file = sorted(assignment_files)[-1]  # Get the most recent file
        
        # Load assignments
        assignments_df = pd.read_csv(assignments_file)
        
        # Convert date column to datetime
        assignments_df['date'] = pd.to_datetime(assignments_df['date'])
        
        # Add a period filter
        period_options = ["All Periods"] + sorted(assignments_df['period'].unique().tolist())
        selected_period = st.selectbox("Select period:", period_options)
        
        # Add worker filter
        worker_options = ["All Workers"] + sorted(assignments_df['worker_name'].unique().tolist())
        selected_worker = st.selectbox("Select worker:", worker_options)
        
        # Filter the data
        filtered_df = assignments_df.copy()
        if selected_period != "All Periods":
            filtered_df = filtered_df[filtered_df['period'] == selected_period]
        
        if selected_worker != "All Workers":
            filtered_df = filtered_df[filtered_df['worker_name'] == selected_worker]
        
        # Get all shifts data for the selected month to show in calendar
        shifts_df = get_shifts_data(year, selected_month_num)
        
        # Display tabs for different views
        tab1, tab2, tab3 = st.tabs(["Calendar View", "List View", "Statistics"])
        
        with tab1:
            st.subheader(f"Calendar for {selected_month} {year}")
            # Draw calendar with assignments
            if filter_by_month := st.checkbox("Filter by selected month", value=True):
                month_filtered_df = filtered_df[filtered_df['date'].dt.month == selected_month_num]
                draw_assignment_calendar(shifts_df, month_filtered_df, selected_month, year, month_names)
            else:
                draw_assignment_calendar(shifts_df, filtered_df, selected_month, year, month_names)
                
            with st.expander("Calendar Legend"):
                st.markdown("""
                - Shifts are shown with their assigned worker
                - Colors indicate shift types (see sidebar)
                - Holidays have pink background
                - Unassigned shifts show without a worker name
                """)
                
        with tab2:
            if not filtered_df.empty:
                # Summary statistics
                st.subheader("Summary")
                total_shifts = len(filtered_df)
                total_hours = filtered_df['hours'].sum()
                night_shifts = filtered_df[filtered_df['section_name'].str.contains('noche', case=False)].shape[0]
                weekend_shifts = filtered_df['is_weekend'].sum()
                festivo_shifts = filtered_df['is_festivo'].sum()
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Shifts", total_shifts)
                col2.metric("Total Hours", f"{total_hours:.1f}")
                col3.metric("Night Shifts", night_shifts)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Weekend Shifts", int(weekend_shifts))
                col2.metric("Holiday Shifts", int(festivo_shifts))
                
                # List view of assignments
                st.subheader("Assignments List")
                
                # Group by date and create a list view
                dates = sorted(filtered_df['date'].unique())
                
                for date in dates:
                    date_assignments = filtered_df[filtered_df['date'] == date]
                    weekday = date.strftime("%A")
                    is_festivo = bool(date_assignments['is_festivo'].iloc[0]) if len(date_assignments) > 0 else False
                    is_weekend = bool(date_assignments['is_weekend'].iloc[0]) if len(date_assignments) > 0 else False
                    
                    date_str = date.strftime("%Y-%m-%d")
                    
                    if is_festivo:
                        header_style = "color: #d32f2f;"
                        day_label = f"{weekday} (Holiday)"
                    elif is_weekend:
                        header_style = "color: #1976d2;"
                        day_label = weekday
                    else:
                        header_style = "color: #212121;"
                        day_label = weekday
                    
                    st.markdown(f"### <span style='{header_style}'>📅 {date_str} - {day_label}</span>", unsafe_allow_html=True)
                    
                    # Display assignments for this day
                    for _, assignment in date_assignments.iterrows():
                        st.markdown(
                            f"""
                            <div style='background-color: {get_shift_color(assignment['section_name'])}; 
                                    color: white; padding: 10px; border-radius: 5px; margin-bottom: 5px;'>
                            <b>{assignment['section_name']}</b>: Assigned to <b>{assignment['worker_name']}</b><br>
                            {assignment['hours']} hours | {"Requires time off after" if assignment['libra'] else "No time off required"}
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    
                    st.markdown("---")
                
        with tab3:
            if not filtered_df.empty:
                # Tabular view
                st.subheader("Tabular View")
                display_df = filtered_df.copy()
                display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
                display_df = display_df.sort_values(by=['date', 'section_name'])
                st.dataframe(display_df[['date', 'day_of_week', 'section_name', 'worker_name', 'hours', 'is_weekend', 'is_festivo', 'period']])
                
                # Worker distribution chart
                st.subheader("Worker Distribution")
                worker_counts = filtered_df['worker_name'].value_counts().reset_index()
                worker_counts.columns = ['Worker', 'Shift Count']
                
                worker_chart = alt.Chart(worker_counts).mark_bar().encode(
                    x=alt.X('Worker:N', sort='-y'),
                    y='Shift Count:Q',
                    color=alt.Color('Worker:N')
                ).properties(
                    width=600,
                    height=400
                )
                
                st.altair_chart(worker_chart, use_container_width=True)
                
                # Period comparison if multiple periods are selected
                if selected_period == "All Periods" and len(filtered_df['period'].unique()) > 1:
                    st.subheader("Period Comparison")
                    
                    # Group by period and calculate metrics
                    period_metrics = filtered_df.groupby('period').agg({
                        'worker_name': 'count',
                        'hours': 'sum',
                        'is_weekend': 'sum',
                        'is_festivo': 'sum'
                    }).reset_index()
                    
                    period_metrics.columns = ['Period', 'Total Shifts', 'Total Hours', 'Weekend Shifts', 'Holiday Shifts']
                    
                    # Display as table and charts
                    st.dataframe(period_metrics)
                    
                    period_chart = alt.Chart(period_metrics.melt(
                        id_vars=['Period'], 
                        value_vars=['Total Shifts', 'Weekend Shifts', 'Holiday Shifts']
                    )).mark_bar().encode(
                        x='Period:N',
                        y='value:Q',
                        color='variable:N',
                        column='variable:N'
                    ).properties(width=150)
                    
                    st.altair_chart(period_chart)
            else:
                st.info("No assignments found with the current filters.")
    
    except Exception as e:
        st.error(f"Error loading assignments: {str(e)}")
        st.info("Make sure the file 'shift_assignments.csv' exists and contains valid data.")