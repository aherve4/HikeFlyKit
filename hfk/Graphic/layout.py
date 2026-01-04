# Copyright (C) 2024 aherve4
# Licensed under the GNU GPL v3.0

from dash import dcc, html
import dash_bootstrap_components as dbc

# --- Components ---

def create_card(title, card_id, icon_class, default_val=None):
    content = default_val if default_val else html.H2(id=card_id, className="card-text")
    header_content = [html.I(className=f"{icon_class} me-2"), title] if icon_class else title
    return dbc.Card(
        dbc.CardBody([
            html.H6(header_content, className="card-subtitle text-muted mb-2"),
            content
        ]),
        className="mb-3 shadow-sm"
    )

def create_stats_card(title, rate_stats, elev_stats, unit="m/h"):
    icon_map = {"Climb": "fas fa-arrow-up", "Descent": "fas fa-arrow-down"}
    icon_class = icon_map.get(title, "")
    header_content = [html.I(className=f"{icon_class} me-2"), title] if icon_class else title
    
    return dbc.Card(
        dbc.CardBody([
            html.H6(header_content, className="card-subtitle text-muted mb-2"),
            # Rate Column
            html.Div([
                html.Strong(f"Rate ({unit}):"),
                html.P(f"Min: {rate_stats['min']} | Avg: {rate_stats['avg']} | Max: {rate_stats['max']}", className="mb-1 small")
            ], className="mb-2"),
            # Elevation Column
            html.Div([
                html.Strong("Elevation (m):"),
                html.P(f"Min: {elev_stats['min']} | Avg: {elev_stats['avg']} | Max: {elev_stats['max']}", className="mb-0 small")
            ])
        ]),
        className="mb-3 shadow-sm h-100"
    )

def create_distance_card(title, dist_stats, icon_class="fas fa-route"):
    header_content = [html.I(className=f"{icon_class} me-2"), title] if icon_class else title
    
    return dbc.Card(
        dbc.CardBody([
            html.H6(header_content, className="card-subtitle text-muted mb-2"),
            html.Div([
                html.Strong("Total Distance per File (km):"),
                html.P(f"Min: {dist_stats['min']} | Avg: {dist_stats['avg']} | Max: {dist_stats['max']}", className="mb-0 small")
            ])
        ]),
        className="mb-3 shadow-sm h-100"
    )

def create_phase_detail_card(title, stats, icon_class):
    header_content = [html.I(className=f"{icon_class} me-2"), title] if icon_class else title
    
    # Count breakdown
    up = stats.get('up_count', 0)
    down = stats.get('down_count', 0)
    total = stats.get('count', 0)
    count_str = f"{total} phases"
    if up > 0 or down > 0:
        parts = []
        if up > 0: parts.append(f"{up} up")
        if down > 0: parts.append(f"{down} down")
        count_str += f" ({', '.join(parts)})"

    return dbc.Card(
        dbc.CardBody([
            html.H6(header_content, className="card-subtitle text-muted mb-2"),
            dbc.Row([
                dbc.Col([
                    html.Strong("Count:"),
                    html.P(count_str, className="mb-1 small"),
                    html.Strong("Elevation:"),
                    html.Div([
                        html.P([html.Strong("D+: ", className="text-secondary"), f"{stats.get('total_climb', 0)} m"], className="mb-0 small"),
                        html.P([html.Strong("D-: ", className="text-secondary"), f"{stats.get('total_descent', 0)} m"], className="mb-0 small"),
                    ]),
                ], width=6),
                dbc.Col([
                    html.Strong("Climb Range:"),
                    html.P(f"{stats.get('climb_range', [0,0])[0]} to {stats.get('climb_range', [0,0])[1]} m/h", className="mb-1 small"),
                    html.Strong("Descent Range:"),
                    html.P(f"{stats.get('descent_range', [0,0])[0]} to {stats.get('descent_range', [0,0])[1]} m/h", className="mb-0 small"),
                ], width=6),
            ])
        ]),
        className="mb-3 shadow-sm h-100"
    )

def create_phase_section(phase):
    # Header styling with phase color
    header_style = {
        "backgroundColor": phase['color'],
        "color": "white",
        "fontWeight": "bold",
        "fontSize": "1.1rem"
    }
    
    # Determine units based on activity type
    rate_unit = "m/s" if phase.get('is_flight', False) else "m/h"
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className=f"{phase['icon']} me-2"),
            phase['title']
        ], style=header_style),
        dbc.CardBody([
            # Timing
            html.Div([
                html.I(className="far fa-clock me-2 text-muted"),
                html.Span(f"{phase['start_time']} → {phase['end_time']}", className="small fw-bold")
            ], className="mb-3 pb-2 border-bottom"),
            
            # 2x2 Grid using Row/Col for info
            dbc.Row([
                # Left Column: Vertical Rates and Altitudes
                dbc.Col([
                    html.Div([
                        html.Small("Altitude", className="text-muted d-block mb-1"),
                        html.P([
                            html.Span(f"Min: {phase['min_alt']} m", className="me-2"),
                            html.Span(f"Max: {phase['max_alt']} m")
                        ], className="mb-2 small fw-bold")
                    ]),
                    html.Div([
                        html.Small(f"Rates ({rate_unit})", className="text-muted d-block mb-1"),
                        html.P([
                            html.Span(f"Climb: {phase['climb_rate']}", className="me-2 text-success"),
                            html.Span(f"Desc: {phase['descent_rate']}", className="text-danger")
                        ], className="mb-0 small fw-bold")
                    ])
                ], width=7),
                
                # Right Column: D+ and D-
                dbc.Col([
                    html.Small("Elevation", className="text-muted d-block mb-1"),
                    html.Div([
                        html.P([html.Strong("D+: "), f"{phase['d_plus']} m"], className="mb-1 small text-success"),
                        html.P([html.Strong("D-: "), f"{phase['d_minus']} m"], className="mb-0 small text-danger"),
                    ], className="fw-bold")
                ], width=5, className="border-start")
            ])
        ])
    ], className="mb-4 shadow-sm h-100 border-0 overflow-hidden")


# --- Page Layouts ---

def format_summary_duration(minutes):
    if minutes <= 0:
        return "0min"
    d = int(minutes // (24 * 60))
    h = int((minutes % (24 * 60)) // 60)
    m = int(minutes % 60)
    parts = []
    if d > 0: parts.append(f"{d}d")
    if h > 0: parts.append(f"{h}h")
    if m > 0 or not parts: parts.append(f"{m}min")
    return " ".join(parts)

def create_trace_type_cards(counts):
    return dbc.Row([
        dbc.Col(create_card("Total Traces", None, "fas fa-layer-group", f"{counts['total']}"), width=6, lg=3),
        dbc.Col(create_card("Hike & Fly", None, "fas fa-mountain", f"{counts['hike_and_fly']}"), width=6, lg=3),
        dbc.Col(create_card("Fly Only", None, "fas fa-paper-plane", f"{counts['fly_only']}"), width=6, lg=3),
        dbc.Col(create_card("Walk Only", None, "fas fa-walking", f"{counts['walk_only']}"), width=6, lg=3),
    ], className="mb-4")

def create_summary_content(stats):
    return html.Div([
        # Row 1: Counts & Classifications
        create_trace_type_cards(stats['counts']),

        dbc.Row([
            # Row 2: Walk Averages
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-hiking me-2"), "Walk Averages"], className="bg-success text-white"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Small("Avg Distance", className="text-muted d-block"),
                                html.H4(f"{stats['averages']['walk_dist']} km", className="mb-0")
                            ], width=3),
                            dbc.Col([
                                html.Small("Avg D+", className="text-muted d-block"),
                                html.H4(f"{stats['averages']['walk_d_plus']} m", className="mb-0")
                            ], width=3),
                            dbc.Col([
                                html.Small("Avg Duration", className="text-muted d-block"),
                                html.H4(format_summary_duration(stats['averages']['walk_duration_min']), className="mb-0")
                            ], width=3),
                            dbc.Col([
                                html.Small("Avg Climb Rate", className="text-muted d-block"),
                                html.H4(f"{stats['averages']['walk_climb_rate']} m/h", className="mb-0")
                            ], width=3),
                        ])
                    ])
                ], className="shadow-sm h-100")
            ], width=12, lg=6, className="mb-4"),

            # Row 3: Flight Averages
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-paper-plane me-2"), "Flight Averages"], className="bg-info text-white"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Small("Avg Duration", className="text-muted d-block"),
                                html.H4(format_summary_duration(stats['averages']['fly_duration_min']), className="mb-0")
                            ], width=3),
                            dbc.Col([
                                html.Small("Avg D+", className="text-muted d-block"),
                                html.H4(f"{stats['averages']['fly_d_plus']} m", className="mb-0")
                            ], width=3),
                            dbc.Col([
                                html.Small("Avg D-", className="text-muted d-block"),
                                html.H4(f"{stats['averages']['fly_d_minus']} m", className="mb-0")
                            ], width=3),
                            dbc.Col([
                                html.Small("Avg Distance", className="text-muted d-block"),
                                html.H4(f"{stats['averages']['fly_dist']} km", className="mb-0")
                            ], width=3),
                        ])
                    ])
                ], className="shadow-sm h-100")
            ], width=12, lg=6, className="mb-4")
        ])
    ])

def get_global_page_layout(service, visualizer):
    files_list = list(service.tracks.keys())
    # Initially all checked
    
    file_list_group = dbc.ListGroup(
        [
            dbc.ListGroupItem(
                dbc.Row([
                    dbc.Col([
                        html.Div(style={
                            "backgroundColor": service.get_file_color(f), 
                            "width": "15px", 
                            "height": "15px", 
                            "marginRight": "10px", 
                            "borderRadius": "3px",
                            "flexShrink": 0
                        }),
                        dbc.Checkbox(
                            id={'type': 'file-check', 'index': f},
                            label=f" {os.path.basename(f)}",
                            value=True,
                            style={"display": "flex", "alignItems": "center", "flexGrow": 1}
                        )
                    ], width=9, className="d-flex align-items-center"),
                    dbc.Col(
                        dbc.ButtonGroup([
                            dbc.Button(
                                html.I(className="fas fa-crosshairs"),
                                id={'type': 'file-focus-btn', 'index': f},
                                color="secondary",
                                size="sm",
                                title="Focus Map"
                            ),
                            dbc.Button(
                                html.I(className="fas fa-chart-line"),
                                id={'type': 'file-view-btn', 'index': f},
                                color="primary",
                                size="sm",
                                title="Analyze File"
                            )
                        ], className="float-end"),
                        width=3
                    )
                ], className="align-items-center"),
                key=f
            ) for f in files_list
        ],
        flush=True,
        className="mb-4"
    )

    return dbc.Container([
        html.H3([html.I(className="fas fa-globe me-2"), "Global Analysis"], className="mb-3"),
        
        dbc.Row([
            # Sidebar: File List
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-folder-open me-2"), "Loaded Files"], className="bg-light"),
                    dbc.CardBody(file_list_group, style={"maxHeight": "600px", "overflowY": "auto"})
                ], className="shadow-sm")
            ], width=12, lg=3),
            
            # Main Content: Map & Stats
            dbc.Col([
                # Global Map
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-map-marked-alt me-2"), "Global Map (Selected Files)"]),
                    dbc.CardBody(
                        dcc.Graph(id='global-map-graph', style={"height": "400px"}, config={'scrollZoom': True})
                    )
                ], className="mb-4 shadow-sm"),
                
                # Mode Tabs
                dbc.Tabs([
                    dbc.Tab(label="Summary", tab_id="summary"),
                    dbc.Tab(label="Detailed", tab_id="detailed"),
                ], id="global-view-tabs", active_tab="summary", className="mb-3"),

                # Global Stats Cards Placeholder (Content populated by callback)
                html.Div(id='global-stats-container')
                
            ], width=12, lg=9)
        ])
    ], fluid=True)

def get_file_page_layout(service, visualizer, file_path):
    stats = service.get_global_stats(file_path)
    file_name = os.path.basename(file_path)
    
    # Elevation content
    elevation_content = html.Div([
        html.P([html.Strong("D+: "), f"{stats.get('total_climb', 0)} m"], className="mb-0 small"),
        html.P([html.Strong("D-: "), f"{stats.get('total_descent', 0)} m"], className="mb-0 small"),
    ])

    # Times content
    times_content = html.Div([
        html.P([html.Strong("Start: "), f"{stats.get('start_time', 'N/A')}"], className="mb-0 small text-primary"),
        html.P([html.Strong("End: "), f"{stats.get('end_time', 'N/A')}"], className="mb-0 small text-danger"),
    ])

    # Altitude content
    altitude_content = html.Div([
        html.P([html.Strong("Min: "), f"{stats.get('min_alt', 0)} m"], className="mb-0 small"),
        html.P([html.Strong("Max: "), f"{stats.get('max_alt', 0)} m"], className="mb-0 small"),
    ])

    return dbc.Container([
        dbc.Row([
            dbc.Col(dbc.Button([html.I(className="fas fa-arrow-left me-2"), "Back to Global"], href="/", color="secondary", className="mb-3"), width="auto"),
            dbc.Col(html.H3([html.I(className="fas fa-file-alt me-2"), f"Analysis: {file_name}"], className="mb-3"))
        ], className="align-items-center"),

        # Top Section: KPI Cards (Row 1)
        dbc.Row([
            dbc.Col(create_card("Date", f"card-{file_path}-date", "far fa-calendar-alt", stats.get("date", "N/A")), width=6, lg=2),
            dbc.Col(create_card("Times", f"card-{file_path}-times", "far fa-clock", times_content), width=6, lg=2),
            dbc.Col(create_card("Duration", f"card-{file_path}-duration", "fas fa-stopwatch", stats.get("duration", "N/A")), width=6, lg=2),
            dbc.Col(create_card("Distance", f"card-{file_path}-distance", "fas fa-arrows-alt-h", f"{stats.get('total_dist', 0)} km"), width=6, lg=2),
            dbc.Col(create_card("Elevation", f"card-{file_path}-elev-kpi", "fas fa-sort-amount-up", elevation_content), width=6, lg=2),
            dbc.Col(create_card("Altitude", f"card-{file_path}-alt-kpi", "fas fa-arrows-alt-v", altitude_content), width=6, lg=2),
        ], className="mb-2"),

        # Detailed Activities (Row 2)
        dbc.Row([
            dbc.Col(create_phase_detail_card("Flight Phases", stats.get("flight_phases", {}), "fas fa-plane"), width=12, lg=6),
            dbc.Col(create_phase_detail_card("Walk Phases", stats.get("walk_phases", {}), "fas fa-hiking"), width=12, lg=6),
        ], className="mb-2"),

        # Content Section
        dbc.Row([
            # Map for this file
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-map me-2"), "Flight Path"]),
                    dbc.CardBody(
                        dcc.Graph(
                            id={'type': 'file-map', 'index': file_path},
                            figure=visualizer.get_map_figure(focus_gps=file_path, files_filter=[file_path], color_phases=True),
                            style={"height": "400px"}
                        )
                    )
                ], className="mb-4 shadow-sm")
            ], width=12),
        ]),

        dbc.Row([
             # Altitude Profile (Full Width)
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-chart-area me-2"), "Altitude Profile (Continuous)"]),
                    dbc.CardBody(
                        dcc.Graph(
                            id={'type': 'file-alt-profile', 'index': file_path},
                            figure=visualizer.get_altitude_profile_figure(file_path),
                            style={"height": "300px"}
                        )
                    )
                ], className="mb-4 shadow-sm")
            ], width=12),
        ]),
        
        # New Phase Details Section
        html.H4([html.I(className="fas fa-list-ul me-2"), "Phase-by-Phase Details"], className="mt-4 mb-3 border-bottom pb-2"),
        dbc.Row([
            dbc.Col(create_phase_section(phase), width=12, md=6, lg=4)
            for phase in visualizer.get_file_phases_details(file_path)
        ])

    ], fluid=True)

# --- Main App Layout ---

import os

def create_layout(service, visualizer):
    layout = html.Div([
        dcc.Location(id='url', refresh=False),
        
        # Consistent Navbar
        dbc.NavbarSimple(
            brand="IGC Analyzer",
            brand_href="/",
            color="primary",
            dark=True,
            className="mb-4"
        ),
        
        # Content Container
        html.Div(id='page-content')
    ])
    return layout