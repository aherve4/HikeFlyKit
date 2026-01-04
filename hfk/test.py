# Copyright (C) 2024 aherve4
# Licensed under the GNU GPL v3.0

import pandas as pd

import plotly.graph_objects as go

# Example GPS coordinates in the Pyrenees
data = {
    'latitude': [42.7952, 42.7960, 42.7965],
    'longitude': [0.3272, 0.3280, 0.3285]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Create a scatter plot on a map
fig = go.Figure(go.Scattermapbox(
    lat=df['latitude'],
    lon=df['longitude'],
    mode='markers+lines',
    marker=go.scattermapbox.Marker(size=9),
    text=['Point 1', 'Point 2', 'Point 3']
))

# Set the map style to IGN
fig.update_layout(
    mapbox_style="open-street-map",
    mapbox=dict(
        center=go.layout.mapbox.Center(
            lat=42.7952,
            lon=0.3272
        ),
        zoom=14
    ),
    margin={"r":0,"t":0,"l":0,"b":0}
)

# Show the plot
fig.show()