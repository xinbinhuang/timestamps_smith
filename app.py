import streamlit as st
import pandas as pd
import pandas_market_calendars as mcal
from datetime import datetime, date, timedelta

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"


def get_short_weeks_with_holidays(start_date, end_date, market_calendar="NYSE"):
    """Identify weeks with holidays (short trading weeks)"""
    import pandas as pd

    cal = mcal.get_calendar(market_calendar)

    # Get trading schedule for a broader range to check full weeks
    # Extend range to include full weeks that might be partially in our date range
    extended_start = pd.to_datetime(start_date) - timedelta(days=pd.to_datetime(start_date).weekday())
    extended_end = pd.to_datetime(end_date) + timedelta(days=6 - pd.to_datetime(end_date).weekday())

    trading_schedule = cal.schedule(start_date=extended_start, end_date=extended_end)
    holidays = cal.holidays().holidays

    short_weeks = []

    # Group by week (Monday to Friday)
    current_date = extended_start

    while current_date <= extended_end:
        # Find Monday of current week
        week_start = current_date - timedelta(days=current_date.weekday())
        week_end = week_start + timedelta(days=4)  # Friday

        # Get all potential trading days for this full week (Mon-Fri)
        full_week_trading_days = trading_schedule[
            (trading_schedule.index.date >= week_start.date()) &
            (trading_schedule.index.date <= week_end.date())
        ]

        # Check for holidays in this week
        week_holidays = [h for h in holidays
                        if week_start.date() <= h <= week_end.date()]

        # Only consider it a short week if:
        # 1. It has fewer than 5 trading days
        # 2. It has at least 1 trading day
        # 3. Some part of the week overlaps with our original date range
        week_overlaps_range = (
            week_start.date() <= pd.to_datetime(end_date).date() and
            week_end.date() >= pd.to_datetime(start_date).date()
        )

        if (len(full_week_trading_days) < 5 and
            len(full_week_trading_days) > 0 and
            week_overlaps_range):

            # Only include trading dates that fall within our original date range
            filtered_trading_dates = [
                d.date() for d in full_week_trading_days.index
                if pd.to_datetime(start_date).date() <= d.date() <= pd.to_datetime(end_date).date()
            ]

            if filtered_trading_dates:  # Only add if there are trading dates in our range
                short_weeks.append({
                    'week_start': week_start.date(),
                    'week_end': week_end.date(),
                    'trading_days': len(full_week_trading_days),  # Full week count
                    'trading_dates': filtered_trading_dates,  # Only dates in range
                    'holidays': week_holidays
                })

        # Move to next week
        current_date = week_start + timedelta(days=7)

    return short_weeks


def generate_timestamps(
    start_date: date,
    end_date: date,
    interval_min: int,
    selected_months=None,
    selected_weekdays=None,
    selected_week_types=None,
    market_calendar="NYSE",
):
    """Generate timestamps with 9:32 AM entry and 9:35-3:59 PM intervals for market trading days"""
    timestamps = []

    # Get market calendar
    cal = mcal.get_calendar(market_calendar)

    # Get trading days in the date range
    trading_schedule = cal.schedule(start_date=start_date, end_date=end_date)

    # If filtering by week types, get the valid dates
    valid_dates = set()
    if selected_week_types and len(selected_week_types) < 3:  # Not all types selected
        short_weeks = get_short_weeks_with_holidays(start_date, end_date, market_calendar)

        # Get short week dates
        short_week_dates = set()
        for week in short_weeks:
            short_week_dates.update(week['trading_dates'])

        # Get week before short week dates
        week_before_short_dates = set()
        for week in short_weeks:
            # Find the week before this short week
            week_start = week['week_start']
            prev_week_start = week_start - timedelta(days=7)
            prev_week_end = prev_week_start + timedelta(days=4)

            # Get trading days for the previous week
            prev_week_trading = trading_schedule[
                (trading_schedule.index.date >= prev_week_start) &
                (trading_schedule.index.date <= prev_week_end)
            ]

            for trading_day in prev_week_trading.index:
                if start_date <= trading_day.date() <= end_date:
                    week_before_short_dates.add(trading_day.date())

        # Get all trading dates in range
        all_trading_dates = set(trading_schedule.index.date)

        # Regular weeks are all dates minus short weeks minus week before short weeks
        regular_week_dates = all_trading_dates - short_week_dates - week_before_short_dates

        # Add selected week types to valid_dates
        if "Short weeks" in selected_week_types:
            valid_dates.update(short_week_dates)
        if "Week before short week" in selected_week_types:
            valid_dates.update(week_before_short_dates)
        if "Regular weeks" in selected_week_types:
            valid_dates.update(regular_week_dates)

    for trading_day in trading_schedule.index:
        current_date = trading_day.date()

        # Filter by week types if specified
        if selected_week_types and len(selected_week_types) < 3 and current_date not in valid_dates:
            continue

        # Filter by selected months if specified
        if selected_months and current_date.month not in selected_months:
            continue

        if selected_weekdays and current_date.weekday() not in selected_weekdays:
            continue

        # Generate interval timestamps from 9:35 AM to 3:59 PM
        start_time = datetime.combine(
            current_date, datetime.min.time().replace(hour=9, minute=30)
        )
        end_time = datetime.combine(
            current_date, datetime.min.time().replace(hour=15, minute=59)
        )

        current_time = start_time
        while current_time <= end_time:
            # if current_time is exactly 9:30 AM, change it to 9:32 AM
            if current_time.hour == 9 and current_time.minute == 30:
                current_time += timedelta(minutes=2)
            timestamps.append(current_time.strftime(TIMESTAMP_FORMAT))
            current_time += timedelta(minutes=interval_min)

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
            "Start Date", value=datetime.now().date(), help="Select the starting date"
        )

    with col2:
        end_date = st.date_input(
            "End Date", value=datetime.now().date(), help="Select the ending date"
        )

    with col3:
        interval_mins = st.number_input(
            "Interval (mins)", value=5, help="Timestamp intervals (mins)"
        )

    # Filters
    col4, col5, col6 = st.columns(3)

    with col4:
        selected_months = st.multiselect(
            "Select Months",
            options=list(range(1, 13)),
            format_func=lambda x: datetime(2023, x, 1).strftime("%B"),
            default=list(range(1, 13)),
            help="Select which months to include",
        )

    with col5:
        weekday_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        selected_weekdays_names = st.multiselect(
            "Select Days of Week",
            options=weekday_options,
            default=weekday_options,
            help="Select which days of the week to include",
        )

        # Convert weekday names to numbers (0=Monday, 6=Sunday)
        weekday_mapping = {name: i for i, name in enumerate(weekday_options)}
        selected_weekdays = [weekday_mapping[name] for name in selected_weekdays_names]

    with col6:
        week_type_options = ["Short weeks", "Week before short week", "Regular weeks"]
        selected_week_types = st.multiselect(
            "Select Week Types",
            options=week_type_options,
            default=week_type_options,
            help="Filter by week type: short weeks (with holidays), weeks before short weeks, or regular weeks"
        )

    # Validate date range
    if start_date > end_date:
        st.error("Start date must be before or equal to end date!")
        return

    # Show short weeks button
    if st.button("🗓️ Show Short Weeks with Holidays"):
        with st.spinner("Finding short weeks..."):
            short_weeks = get_short_weeks_with_holidays(start_date, end_date)
        
        if short_weeks:
            st.subheader(f"📅 Short Weeks Found: {len(short_weeks)}")
            
            for week in short_weeks:
                with st.expander(f"Week of {week['week_start']} ({week['trading_days']} trading days)"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Trading Days:**")
                        for trading_date in week['trading_dates']:
                            st.write(f"• {trading_date}")
                    
                    with col2:
                        if week['holidays']:
                            st.write("**Holidays:**")
                            for holiday in week['holidays']:
                                st.write(f"• {holiday}")
                        else:
                            st.write("**No holidays found**")
        else:
            st.info("No short weeks found in the selected date range.")

    # Generate timestamps button
    col_gen1, col_gen2 = st.columns(2)

    with col_gen1:
        if st.button("Generate Timestamps", type="primary"):
            with st.spinner("Generating timestamps..."):
                timestamps = generate_timestamps(
                    start_date, end_date, interval_mins, selected_months, selected_weekdays,
                    selected_week_types
                )

            if timestamps:
                # Create DataFrame
                df = pd.DataFrame({"OPEN_DATETIME": timestamps})

                # Display info
                st.success(f"Generated {len(timestamps)} timestamps")
                st.info(f"Date range: {start_date} to {end_date}")
                st.info(
                    f"Time range: 9:35 AM to 3:55 PM ({interval_mins}-minute intervals)"
                )

                # Display filter info
                if len(selected_months) < 12:
                    month_names = [
                        datetime(2023, m, 1).strftime("%B") for m in selected_months
                    ]
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
                    help="Download the generated timestamps as a CSV file",
                )

            else:
                st.warning("No timestamps generated. Please check your date range.")

    with col_gen2:
        if st.button("📅 Show Dates Only"):
            with st.spinner("Generating dates..."):
                timestamps = generate_timestamps(
                    start_date, end_date, interval_mins, selected_months, selected_weekdays,
                    selected_week_types
                )

            if timestamps:
                # Extract unique dates from timestamps
                unique_dates = set()
                for timestamp in timestamps:
                    date_part = timestamp.split(' ')[0]  # Get date part before space
                    unique_dates.add(date_part)

                # Sort dates
                sorted_dates = sorted(list(unique_dates))
                dates_string = ",".join(sorted_dates)

                st.subheader(f"📅 Selected Dates ({len(sorted_dates)} dates in ISO format)")
                st.code(dates_string, language=None, wrap_lines=True)

            else:
                st.warning("No dates generated. Please check your date range.")


if __name__ == "__main__":
    main()
