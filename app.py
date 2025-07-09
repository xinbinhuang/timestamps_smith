import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def generate_timestamps(start_date, end_date, interval_min):
    """Generate 5-minute interval timestamps between 9:35 AM and 3:55 PM for each day"""
    timestamps = []
    
    # Convert to datetime objects if they're date objects
    if hasattr(start_date, 'date'):
        start_date = start_date.date()
    if hasattr(end_date, 'date'):
        end_date = end_date.date()
    
    current_date = start_date
    
    while current_date <= end_date:
        # Start time: 9:35 AM
        start_time = datetime.combine(current_date, datetime.min.time().replace(hour=9, minute=35))
        # End time: 3:55 PM
        end_time = datetime.combine(current_date, datetime.min.time().replace(hour=15, minute=55))
        
        current_time = start_time
        
        while current_time <= end_time:
            timestamps.append(current_time.strftime("%Y-%m-%d %H:%M"))
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
    
    # Validate date range
    if start_date > end_date:
        st.error("Start date must be before or equal to end date!")
        return
    
    # Generate timestamps button
    if st.button("Generate Timestamps", type="primary"):
        with st.spinner("Generating timestamps..."):
            timestamps = generate_timestamps(start_date, end_date, interval_mins)
        
        if timestamps:
            # Create DataFrame
            df = pd.DataFrame({'OPEN_DATETIME': timestamps})
            
            # Display info
            st.success(f"Generated {len(timestamps)} timestamps")
            st.info(f"Date range: {start_date} to {end_date}")
            st.info(f"Time range: 9:35 AM to 3:55 PM ({interval_mins}-minute intervals)")
            
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