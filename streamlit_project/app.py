### Import Libraries
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

### Config
st.set_page_config(
    page_title="GetAround Delay",
    page_icon=":oncoming_automobile:",
    layout="wide",
)

### Load Data
DATA = "get_around_delay_analysis (1).xlsx"

@st.cache_data
def load_data():
    data = pd.read_excel(DATA)
    return data

data_load_state = st.text("Loading data...")  # display message
data = load_data()
data_load_state.text("")  # stop when the data is loaded

### Header with Image
image = Image.open("logo.png")  # Load the image
st.image(image, width=700)  # Display the image

### Title
st.title("GetAround Delay Analysis :clock5: :car: :dash: ")

# Data Cleaning (replace NaN by 0 when checkout is ended)
mask = data["state"] == "ended"
data["delay_at_checkout_in_minutes"] = data[mask]["delay_at_checkout_in_minutes"].fillna(0)

### Delay Categorization
st.markdown("<h2 style='text-decoration: underline;'>Delay Categorization</h2>", unsafe_allow_html=True)

st.markdown("""
The time slots will be defined in minutes, and here is how we will organize them:
- Early Returns : Less than 0 minutes (the vehicle is returned before the scheduled time).
- Very Minor : 0 to 15 minutes
- Minor : 15 to 60 minutes
- Moderate : 60 to 180 minutes
- Serious : 180 to 600 minutes
- Very Serious : 600 to 1440 minutes (24 hours)
- Extreme : More than 1440 minutes
""", unsafe_allow_html=True)

# Define time slots and labels
bins = [-1000000, 0, 15, 60, 180, 600, 1440, 1000000]
labels = ['Early Returns', 'Very Minor', 'Minor', 'Moderate', 'Serious', 'Very Serious(10 to 24h)', 'Extreme(more than 24h)']

# Application des tranches au DataFrame et création de la nouvelle colonne
data['delay category'] = pd.cut(data['delay_at_checkout_in_minutes'], bins=bins, labels=labels)

# Compter les occurrences dans chaque catégorie de retard
category_counts = data['delay category'].value_counts().sort_index()

if st.checkbox('Show raw data', key='raw_data'):
    st.subheader('Raw data')
    st.write(data) 

# Visualize delay categories with Plotly
fig = px.bar(category_counts, x=category_counts.index, y=category_counts.values, 
             labels={'x':'Delay Category', 'y':'Number of Delays'}, 
             title='Distribution of Delay Categories',
             color=category_counts.index,
             color_discrete_sequence=px.colors.qualitative.G10)
st.plotly_chart(fig)

### Mean per checking type
st.markdown("***")
st.markdown("<h2 style='text-decoration: underline;'> Average Delay per Checking Type </h2>", unsafe_allow_html=True)
mean_per_checking_type = data.groupby("checkin_type",  observed=True)["delay_at_checkout_in_minutes"].mean().reset_index()
st.write(mean_per_checking_type)

average_delay = round(data[data["state"] == "ended"]["delay_at_checkout_in_minutes"].mean())
st.write(f"The Average Delay is {average_delay} Minutes.")

fig = px.bar(mean_per_checking_type, x='checkin_type', y='delay_at_checkout_in_minutes', 
             labels={'x':'Check-in Type', 'y':'Average Delay (minutes)'}, 
             title='Average Delay at Checkout by Checkin Type',
             color='checkin_type',
             color_discrete_sequence=px.colors.qualitative.G10)
st.plotly_chart(fig, theme="streamlit", use_container_width=True)

st.markdown("<h2 style='text-decoration: underline;'>Most Common Check-in Types</h2>", unsafe_allow_html=True)
checkin_types = data.groupby("checkin_type")["checkin_type"].value_counts()

### Type of cars and state of booking distributions
st.markdown("***")
st.write("**Check-in Types and State of Booking Distributions:**")

pie = make_subplots(
    rows=1,
    cols=2,
    specs=[[{"type": "domain"}, {"type": "domain"}]],
    shared_yaxes=True,
    subplot_titles=["Type of Check-in", "State of booking"],
)

pie.add_trace(
    go.Pie(
        values=data["checkin_type"].value_counts(normalize=True),
        labels=data["checkin_type"].value_counts(normalize=True).index,
        marker_colors=px.colors.qualitative.Pastel,
    ),
    row=1,
    col=1,
)

pie.add_trace(
    go.Pie(
        values=data["state"].value_counts(normalize=True).round(3),
        labels=data["state"].value_counts(normalize=True).index,
        marker_colors=px.colors.qualitative.Pastel2,
    ),
    row=1,
    col=2,
)
pie.update_traces(hole=0.4, textinfo="label+percent")
pie.update_layout(width=1200, legend=dict(font=dict(size=16)))
st.plotly_chart(pie)

### Delay Distribution by Check-in Method
st.markdown("***")
st.markdown("<h2 style='text-decoration: underline;'>Delay Distribution by Check-in Method </h2>", unsafe_allow_html=True)

delay_by_checkin_type = data.groupby(['checkin_type', 'delay category'], observed=True).size().reset_index(name='counts')

fig = px.bar(delay_by_checkin_type, x='checkin_type', y='counts', color='delay category',
             labels={'counts': 'Number of Delays', 'checkin_type': 'Check-in Type', 'delay category': 'Delay Category'},
             title='Delay Distribution by Check-in Type',
             barmode='group',
             color_discrete_sequence=px.colors.qualitative.G10)

st.plotly_chart(fig, use_container_width=True)

# Vérification des indices
mask_connect = data["checkin_type"] == "connect"
mask_ended = data["state"] == "ended"

## Ensure masks are aligned with data index
mask_connect = mask_connect.reindex(data.index, fill_value=False)
mask_ended = mask_ended.reindex(data.index, fill_value=False)

### Revenue impact analysis
st.markdown("***")
st.markdown("<h2 style='text-decoration: underline;'>Revenue Impact and Problematic Cases Resolved by Threshold </h2>", unsafe_allow_html=True)

# Sélection du seuil par l'utilisateur
threshold = st.select_slider("Choose a Threshold on Connect feature only: ", options=[60, 120, 240, 570, 720], key='threshold_selector')

# Filtrage des données en fonction du seuil
data_delta_not_null = data[data["time_delta_with_previous_rental_in_minutes"].notnull()]
data_delta_not_null_new = data_delta_not_null.drop(
    data_delta_not_null[
        (data_delta_not_null["checkin_type"] == "connect")
        & (
            data_delta_not_null["time_delta_with_previous_rental_in_minutes"]
            <= threshold
        )
    ].index
)

# Revenue Impact Calculation
mask_connect = data_delta_not_null["checkin_type"] == "connect"
mask_ended = data_delta_not_null["state"] == "ended"
mask_connect_new = data_delta_not_null_new["checkin_type"] == "connect"
mask_ended_new = data_delta_not_null_new["state"] == "ended"

diff = (
    data_delta_not_null[mask_connect & mask_ended]["state"].count()
    - data_delta_not_null_new[mask_connect_new & mask_ended_new]["state"].count()
)

percentage_affected = ((diff / data.shape[0]) * 100).round(2)

st.write(
    "It will potentially affect ",
    percentage_affected,
    "% of our owner's revenue for a threshold of ",
    threshold,
    " minutes.",
)

st.write(
    data_delta_not_null_new.groupby(["checkin_type", "state"], observed=False)[
        "time_delta_with_previous_rental_in_minutes"
    ].describe()
)

# Problematic Cases Resolved Calculation
mask_canceled = data_delta_not_null["state"] == "canceled"
mask_canceled_new = data_delta_not_null_new["state"] == "canceled"

diff2 = (
    data_delta_not_null[mask_canceled]["state"].count()
    - data_delta_not_null_new[mask_canceled_new]["state"].count()
)

st.write(
    "It will potentially resolve ",
    diff2,
    " problematic cases for a threshold of ",
    threshold,
    " minutes.",
)

# Visualisation des cas problématiques résolus par seuil
thresholds = [60, 120, 240, 570, 720]
problematic_cases_resolved = []

for t in thresholds:
    data_delta_not_null_new = data_delta_not_null.drop(
        data_delta_not_null[
            (data_delta_not_null["checkin_type"] == "connect")
            & (
                data_delta_not_null["time_delta_with_previous_rental_in_minutes"]
                <= t
            )
        ].index
    )
    mask_canceled = data_delta_not_null["state"] == "canceled"
    mask_canceled_new = data_delta_not_null_new["state"] == "canceled"
    diff2 = (
        data_delta_not_null[mask_canceled]["state"].count()
        - data_delta_not_null_new[mask_canceled_new]["state"].count()
    )
    problematic_cases_resolved.append(diff2)

fig2 = px.bar(
    x=thresholds, 
    y=problematic_cases_resolved, 
    labels={'x': 'Threshold (minutes)', 'y': 'Problematic Cases Resolved'},
    title='Number of Problematic Cases Resolved by Chosen Threshold'
)

st.plotly_chart(fig2, use_container_width=True)

### Analysis of Driver's Delays and Impact
st.markdown("***")
st.markdown("<h2 style='text-decoration: underline;'>Frequency of Late Check-ins by Type </h2>", unsafe_allow_html=True)
count = data[data["state"] == "ended"].shape[0]
late_drivers = round((data["delay_at_checkout_in_minutes"] > 0).sum() / count, 2) * 100
st.write(f"{late_drivers}% of drivers are late for the next check-in.")

late_by_checkin = data[data['delay_at_checkout_in_minutes'] > 0].groupby('checkin_type').size().reset_index(name='late_checkin_count')

fig = px.bar(late_by_checkin, x='checkin_type', y='late_checkin_count', 
             title='Frequency of Late Check-ins by Method',
             labels={'checkin_type': 'Check-in Method', 'late_checkin_count': 'Count of Late Check-ins'},
             color='checkin_type',
             color_discrete_sequence=px.colors.qualitative.G10)  

st.plotly_chart(fig, theme="streamlit", use_container_width=True)
