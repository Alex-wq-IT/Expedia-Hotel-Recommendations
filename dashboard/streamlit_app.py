"""Portable demo dashboard over prebuilt Expedia MART CSV snapshots.

This is intentionally separate from the production Superset deployment.
It is useful for project defense when ClickHouse/Superset are unavailable.
"""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "marts"

st.set_page_config(page_title="Expedia Hotel Analytics", page_icon="🏨", layout="wide")
st.sidebar.title("Expedia Hotel Analytics")
data_dir = Path(st.sidebar.text_input("MART CSV directory", str(DEFAULT_DATA))).expanduser()
page = st.sidebar.radio(
    "Раздел",
    ["Executive", "Channels & Mobile", "Destinations", "Customer & Retention",
     "Trips & Package", "Data Quality"],
)

@st.cache_data(show_spinner=False)
def load(name: str) -> pd.DataFrame:
    path = data_dir / f"{name}.csv"
    if not path.is_file():
        raise FileNotFoundError(
            f"Не найден {path}. Укажите каталог с 14 CSV-витринами в sidebar."
        )
    return pd.read_csv(path)

def ratio(numerator, denominator) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0

st.title("Expedia Hotel Recommendations — аналитические витрины")
st.caption(
    "Dashboard читает только готовые MARTS. "
    "Encoded ID не интерпретируются как реальные географические названия."
)

try:
    if page == "Executive":
        product = load("mart_product_daily")
        sessions = load("mart_session_daily")
        product["date_key"] = pd.to_datetime(product["date_key"])
        sessions["date_key"] = pd.to_datetime(sessions["date_key"])
        bookings = int(product["bookings"].sum())
        row_events = int(product["row_events"].sum())
        weighted_events = int(product["weighted_events"].sum())
        users = int(load("mart_booking_frequency")["users"].sum())
        session_count = int(sessions["sessions"].sum())
        booking_sessions = int(sessions["booking_sessions"].sum())

        cols = st.columns(6)
        cols[0].metric("Event rows", f"{row_events:,.0f}")
        cols[1].metric("Weighted events", f"{weighted_events:,.0f}", help="SUM(cnt)")
        cols[2].metric("Bookings", f"{bookings:,.0f}")
        cols[3].metric("Booking row conversion", f"{ratio(bookings,row_events):.2%}")
        cols[4].metric("Users", f"{users:,.0f}")
        cols[5].metric("Session booking rate", f"{ratio(booking_sessions,session_count):.2%}")

        daily = product.sort_values("date_key")
        st.plotly_chart(px.line(daily, x="date_key", y="bookings",
                                title="Bookings by day"), use_container_width=True)
        daily_rate = daily[["date_key","bookings","row_events"]].copy()
        daily_rate["conversion"] = daily_rate["bookings"]/daily_rate["row_events"]
        st.plotly_chart(px.line(daily_rate, x="date_key", y="conversion",
                                title="Booking row conversion by day"),
                        use_container_width=True)

    elif page == "Channels & Mobile":
        channel = load("mart_channel_platform")
        channel["channel"] = channel["channel"].astype(str)
        agg = channel.groupby(["channel","is_mobile"],as_index=False).agg(
            row_events=("row_events","sum"), bookings=("bookings","sum"))
        agg["conversion"] = agg["bookings"]/agg["row_events"]
        c1,c2 = st.columns(2)
        c1.plotly_chart(px.bar(agg,x="channel",y="bookings",color="is_mobile",
                               barmode="group",title="Bookings by channel"),
                        use_container_width=True)
        c2.plotly_chart(px.bar(agg,x="channel",y="conversion",color="is_mobile",
                               barmode="group",title="Conversion by channel"),
                        use_container_width=True)
        mobile = channel.groupby("is_mobile",as_index=False).agg(
            row_events=("row_events","sum"), bookings=("bookings","sum"))
        mobile["conversion"] = mobile["bookings"]/mobile["row_events"]
        st.dataframe(mobile,use_container_width=True,hide_index=True)

    elif page == "Destinations":
        dest = load("mart_destination_performance")
        qualified = dest[
            dest["meets_min_volume_flag"].astype(bool)
            & dest["meets_booking_min_volume_flag"].astype(bool)
        ].copy()
        volume = qualified.groupby("destination_id",as_index=False).agg(
            row_events=("row_events","sum"), bookings=("bookings","sum"))
        volume["conversion"] = volume["bookings"]/volume["row_events"]
        c1,c2=st.columns(2)
        c1.plotly_chart(px.bar(volume.nlargest(20,"bookings"),
                               x="destination_id",y="bookings",
                               title="Top destination IDs by bookings"),
                        use_container_width=True)
        c2.plotly_chart(px.bar(volume[volume["row_events"]>=1000].nlargest(20,"conversion"),
                               x="destination_id",y="conversion",
                               title="Top qualified destination IDs by conversion"),
                        use_container_width=True)
        st.info("Destination IDs закодированы: реальные названия без lookup не присваиваются.")

    elif page == "Customer & Retention":
        freq=load("mart_booking_frequency").sort_values("booking_count_bucket_order")
        ret=load("mart_retention_cohort")
        exact=load("mart_booking_frequency_exact")
        c1,c2=st.columns(2)
        c1.plotly_chart(px.bar(freq,x="booking_count_bucket",y="users",
                               title="Booking-frequency segments"),
                        use_container_width=True)
        rc=ret.groupby("months_since_first_booking",as_index=False).agg(
            cohort_users=("cohort_users","sum"),
            returned_bookers=("returned_bookers","sum"))
        rc["retention"]=rc["returned_bookers"]/rc["cohort_users"]
        c2.plotly_chart(px.line(rc,x="months_since_first_booking",y="retention",
                                markers=True,title="Observed repeat-booking retention"),
                        use_container_width=True)
        st.plotly_chart(px.bar(exact[exact["bookings"]<=20],x="bookings",y="users",
                               title="Users by exact observed booking count (0–20)"),
                        use_container_width=True)

    elif page == "Trips & Package":
        trip=load("mart_trip_profile")
        package=load("mart_package_profile")
        calendar=load("mart_travel_calendar_daily")
        lead=trip.groupby("lead_time_bucket",as_index=False).agg(
            events=("events","sum"),bookings=("bookings","sum"))
        lead["conversion"]=lead["bookings"]/lead["events"]
        stay=trip.groupby("stay_length_bucket",as_index=False).agg(
            events=("events","sum"),bookings=("bookings","sum"))
        stay["conversion"]=stay["bookings"]/stay["events"]
        pack=package.groupby("is_package",as_index=False).agg(
            events=("events","sum"),bookings=("bookings","sum"))
        pack["conversion"]=pack["bookings"]/pack["events"]
        c1,c2=st.columns(2)
        c1.plotly_chart(px.bar(lead,x="lead_time_bucket",y="conversion",
                               title="Conversion by lead-time bucket"),
                        use_container_width=True)
        c2.plotly_chart(px.bar(stay,x="stay_length_bucket",y="conversion",
                               title="Conversion by stay-length bucket"),
                        use_container_width=True)
        st.plotly_chart(px.bar(pack,x="is_package",y="conversion",
                               title="Package vs non-package conversion"),
                        use_container_width=True)
        calendar["full_date"]=pd.to_datetime(calendar["full_date"])
        st.plotly_chart(px.line(calendar.sort_values("full_date"),x="full_date",
                                y=["checkins_on_date","checkouts_on_date"],
                                title="Travel calendar: check-ins/check-outs"),
                        use_container_width=True)

    elif page == "Data Quality":
        quality=load("mart_data_quality_daily")
        distance=load("mart_distance_quality")
        quality["date_key"]=pd.to_datetime(quality["date_key"])
        q=quality.melt("date_key",
            value_vars=["missing_distance_share","imputed_distance_share",
                        "invalid_lead_time_share","invalid_stay_share",
                        "quality_issue_share"],
            var_name="metric",value_name="share")
        st.plotly_chart(px.line(q,x="date_key",y="share",color="metric",
                                title="Daily data-quality shares"),
                        use_container_width=True)
        st.plotly_chart(px.scatter(distance,x="coverage_pct",y="mae",
                                   color="imputation_level",size="average_support",
                                   hover_data=["min_support"],
                                   title="Distance imputation: coverage vs MAE"),
                        use_container_width=True)
except FileNotFoundError as exc:
    st.error(str(exc))
