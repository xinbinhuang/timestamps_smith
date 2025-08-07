import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"

def generate_timestamps(start_date: date, end_date: date, interval_min: int, selected_months=None, selected_weekdays=None):
    """Generate timestamps with 9:32 AM entry and 9:35-3:59 PM intervals for each day, filtered by month and weekday"""
    timestamps = []
    
    current_date = start_date
    while current_date <= end_date:
        if selected_months and current_date.month not in selected_months:
            current_date += timedelta(days=1)
            continue
            
        if selected_weekdays and current_date.weekday() not in selected_weekdays:
            current_date += timedelta(days=1)
            continue
        
        # Add 9:32 AM timestamp
        open_timestamp = datetime.combine(current_date, datetime.min.time().replace(hour=9, minute=32))
        timestamps.append(open_timestamp.strftime(TIMESTAMP_FORMAT))

        # Generate interval timestamps from 9:35 AM to 3:59 PM
        start_time = datetime.combine(current_date, datetime.min.time().replace(hour=9, minute=35))
        end_time = datetime.combine(current_date, datetime.min.time().replace(hour=15, minute=59))
        
        current_time = start_time
        while current_time <= end_time:
            timestamps.append(current_time.strftime(TIMESTAMP_FORMAT))
            current_time += timedelta(minutes=interval_min)
        
        current_date += timedelta(days=1)
    
    return timestamps

@st.cache_data
def convert_for_download(df):
    return df.to_csv(index=False).encode("utf-8")

def main():
    st.title("📅 🔨 Timestamps Smith")
    st.markdown("Generate timestamps between 9:35 AM and 3:55 PM")
    
    # Date range selector
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now().date(),
            help="Select the starting date"
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now().date(),
            help="Select the ending date"
        )
    
    with col3:
        interval_mins = st.number_input(
            "Interval (mins)",
            value=5,
            help="Timestamp intervals (mins)"
        )
    
    # Filters
    col4, col5 = st.columns(2)
    
    with col4:
        selected_months = st.multiselect(
            "Select Months",
            options=list(range(1, 13)),
            format_func=lambda x: datetime(2023, x, 1).strftime("%B"),
            default=list(range(1, 13)),
            help="Select which months to include"
        )
    
    with col5:
        weekday_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        selected_weekdays_names = st.multiselect(
            "Select Days of Week",
            options=weekday_options,
            default=weekday_options,
            help="Select which days of the week to include"
        )
        
        # Convert weekday names to numbers (0=Monday, 6=Sunday)
        weekday_mapping = {name: i for i, name in enumerate(weekday_options)}
        selected_weekdays = [weekday_mapping[name] for name in selected_weekdays_names]
    
    # Validate date range
    if start_date > end_date:
        st.error("Start date must be before or equal to end date!")
        return
    
    # Generate timestamps button
    if st.button("Generate Timestamps", type="primary"):
        with st.spinner("Generating timestamps..."):
            timestamps = generate_timestamps(start_date, end_date, interval_mins, selected_months, selected_weekdays)
        
        if timestamps:
            # Create DataFrame
            df = pd.DataFrame({'OPEN_DATETIME': timestamps})
            
            # Display info
            st.success(f"Generated {len(timestamps)} timestamps")
            st.info(f"Date range: {start_date} to {end_date}")
            st.info(f"Time range: 9:35 AM to 3:55 PM ({interval_mins}-minute intervals)")
            
            # Display filter info
            if len(selected_months) < 12:
                month_names = [datetime(2023, m, 1).strftime("%B") for m in selected_months]
                st.info(f"Months: {', '.join(month_names)}")
            
            if len(selected_weekdays_names) < 7:
                st.info(f"Days: {', '.join(selected_weekdays_names)}")
            
            # Show preview
            st.subheader("Preview (First 20 rows)")
            st.dataframe(df.head(20))
            
            # Download button
            st.download_button(
                label="📥 Download CSV",
                data=convert_for_download(df),
                file_name=f"timestamps_{start_date}_to_{end_date}_{interval_mins}mins.csv",
                mime="text/csv",
                help="Download the generated timestamps as a CSV file"
            )
            
        else:
            st.warning("No timestamps generated. Please check your date range.")

if __name__ == "__main__":
    main()