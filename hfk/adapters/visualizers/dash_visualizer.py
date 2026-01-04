# Copyright (C) 2024 aherve4
# Licensed under the GNU GPL v3.0

import os
import plotly.graph_objects as go
import plotly.colors
from ...Graphic.igcgraph import IgcGraph
from ...application.collection_service import TrackCollectionService

class DashVisualizer:
    """Adapter to generate Dash-compatible Plotly figures from the collection service."""
    
    def __init__(self, service: TrackCollectionService):
        self.service = service

    def get_performance_landscape_figure(self, files_filter=None, phase_type='flight', metric_type="climb"):
        fig = IgcGraph.new_figure()
        
        for file_path in self.service.tracks:
            if files_filter is not None and file_path not in files_filter:
                continue
            
            logical_phases = self.service.get_logical_phases(file_path)
            target_is_f = (phase_type == 'flight')
            
            x_vals, y_vals, hover_text = [], [], []
            
            for i, lp in enumerate(logical_phases):
                if lp.is_flight != target_is_f: continue
                
                rate = lp.climb_rate_val if metric_type == "climb" else lp.descent_rate_val
                elev = lp.d_plus if metric_type == "climb" else lp.d_minus
                
                if rate == 0 and elev == 0: continue
                
                x_vals.append(rate)
                y_vals.append(elev)
                hover_text.append(
                    f"File: {os.path.basename(file_path)}<br>"
                    f"Activity: {lp.type_label} {i+1}<br>"
                    f"Avg Rate: {rate} {'m/s' if target_is_f else 'm/h'}<br>"
                    f"Elevation: {elev} m"
                )
            
            if x_vals:
                color = self.service.get_file_color(file_path)
                fig.add_trace(go.Scatter(
                    x=x_vals, y=y_vals, mode='markers',
                    marker=dict(size=10, color=color, opacity=0.8, line=dict(width=1, color='white')),
                    name=os.path.basename(file_path),
                    text=hover_text, hoverinfo='text'
                ))
        
        unit = "m/s" if phase_type == 'flight' else "m/h"
        y_label = "D+ (m)" if metric_type == "climb" else "D- (m)"
        fig.update_layout(
            title=dict(text=f"{phase_type.capitalize()} {metric_type.capitalize()} Performance", x=0.5),
            xaxis=dict(title=dict(text=f"Avg Rate ({unit})"), rangemode="nonnegative"),
            yaxis=dict(title=dict(text=y_label), rangemode="nonnegative"),
            showlegend=True, hovermode='closest', margin=dict(l=40, r=40, t=60, b=40)
        )
        return fig

    def get_map_figure(self, focus_gps=None, files_filter=None, color_phases=False):
        fig = IgcGraph.new_figure()
        all_lats, all_lons = [], []
        focus_center = None
        
        for file_path, track in self.service.tracks.items():
            if files_filter is not None and file_path not in files_filter: continue
            
            df = track.dataframe
            if not df.empty:
                all_lats.extend([df['Lat'].min(), df['Lat'].max()])
                all_lons.extend([df['Long'].min(), df['Long'].max()])
                if file_path == focus_gps:
                    focus_center = dict(lat=df['Lat'].iloc[0], lon=df['Long'].iloc[0])

            if color_phases and file_path == focus_gps:
                logical_phases = self.service.get_logical_phases(file_path)
                colors = plotly.colors.qualitative.Plotly * (len(logical_phases) // 10 + 1)
                for i, lp in enumerate(logical_phases):
                    plot = IgcGraph.generate_map_plot(lp.dataframe, name=f"{lp.type_label} {i+1}", color=colors[i])
                    plot.showlegend = True
                    fig.add_trace(plot)
            else:
                color = self.service.get_file_color(file_path)
                plot = IgcGraph.generate_map_plot(df, name=os.path.basename(file_path), color=color)
                plot.showlegend = False
                fig.add_trace(plot)
        
        # Center/Zoom logic
        layout_center = dict(lat=42.7952, lon=0.3272)
        zoom = 6
        if focus_center:
            layout_center, zoom = focus_center, 13
        elif all_lats and all_lons:
            layout_center = dict(lat=(min(all_lats)+max(all_lats))/2, lon=(min(all_lons)+max(all_lons))/2)
            zoom = 10

        fig.update_layout(
            mapbox_style="open-street-map",
            mapbox=dict(center=go.layout.mapbox.Center(lat=layout_center['lat'], lon=layout_center['lon']), zoom=zoom),
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        return fig

    def get_altitude_profile_figure(self, file_path):
        fig = IgcGraph.new_figure()
        if file_path in self.service.tracks:
            logical_phases = self.service.get_logical_phases(file_path)
            colors = plotly.colors.qualitative.Plotly * (len(logical_phases) // 10 + 1)
            for i, lp in enumerate(logical_phases):
                plot = IgcGraph.generate_line_plot(xVal=lp.dataframe.index, yVal=lp.dataframe['Alt_gps'], series_name=f"{lp.type_label} {i+1}", color=colors[i])
                plot.showlegend = True
                fig.add_trace(plot)
            fig.update_layout(xaxis=dict(title=dict(text="Time")), yaxis=dict(title=dict(text="Altitude (m)")), hovermode="x unified")
        return fig

    def get_file_phases_details(self, file_path):
        details = []
        if file_path in self.service.tracks:
            logical_phases = self.service.get_logical_phases(file_path)
            colors = plotly.colors.qualitative.Plotly * (len(logical_phases) // 10 + 1)
            for i, lp in enumerate(logical_phases):
                details.append({
                    "title": f"{lp.type_label} {i+1}", "icon": lp.icon, "color": colors[i],
                    "start_time": lp.start_time, "end_time": lp.end_time,
                    "min_alt": lp.min_alt, "max_alt": lp.max_alt,
                    "climb_rate": lp.climb_rate, "descent_rate": lp.descent_rate,
                    "d_plus": round(lp.d_plus, 0), "d_minus": round(lp.d_minus, 0),
                    "is_flight": lp.is_flight
                })
        return details
