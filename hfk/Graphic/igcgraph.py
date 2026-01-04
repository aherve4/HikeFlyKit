# Copyright (C) 2024 aherve4
# Licensed under the GNU GPL v3.0

"""
IgcGraph class plots graphes from IGC data
"""

import plotly.express as px
import plotly.graph_objects as go

class IgcGraph():
    @staticmethod
    def new_figure():
        return go.Figure(layout=dict(barcornerradius=15))

    @staticmethod
    def generate_bar_plot(xVal: list, 
                          yVal:list, 
                          series_name:str = "",
                          marker_color=None):
        return go.Bar(x=xVal, 
                      y=yVal, 
                      name=series_name,
                      marker_color=marker_color,
                      hovertemplate="File=%s<br>Phase=%%{x}<br>Value=%%{y}<extra></extra>"% series_name)

    @staticmethod
    def generate_line_plot(xVal, yVal, series_name="", color=None):
        return go.Scatter(
            x=xVal,
            y=yVal,
            mode='lines',
            name=series_name,
            line=dict(color=color),
            hovertemplate="Time=%{x}<br>Alt=%{y}m<extra></extra>"
        )

    @staticmethod
    def generate_map_plot(df, name="", color=None):
        plot = go.Scattermapbox(
            lat=df['Lat'],
            lon=df['Long'],
            mode='markers+lines',
            marker=go.scattermapbox.Marker(size=5, color=color),
            line=dict(color=color),
            name=name,
            hovertemplate=f"<b>{name}</b><extra></extra>"
        )
        return plot