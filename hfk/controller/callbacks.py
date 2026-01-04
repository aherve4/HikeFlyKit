# Copyright (C) 2024 aherve4
# Licensed under the GNU GPL v3.0

from dash import Input, Output, State, ALL, MATCH, ctx, html
import dash_bootstrap_components as dbc
import urllib.parse
from hfk.Graphic.layout import get_global_page_layout, get_file_page_layout, create_stats_card, create_card

def register_callbacks(app, service, visualizer):
    
    # --- ROUTING CALLBACK ---
    @app.callback(
        Output('page-content', 'children'),
        Input('url', 'pathname')
    )
    def display_page(pathname):
        if not pathname:
            return get_global_page_layout(service, visualizer)
            
        decoded_path = urllib.parse.unquote(pathname)
        
        if decoded_path == "/":
            return get_global_page_layout(service, visualizer)
        elif decoded_path.startswith("/file/"):
            # Extract filename from path
            file_path = decoded_path.replace("/file/", "")
            return get_file_page_layout(service, visualizer, file_path)
        else:
            return dbc.Container(html.H1("404: Not found", className="text-danger"))

    # --- GLOBAL PAGE CALLBACKS ---
    
    # Navigate to file detail when "Analyze" button is clicked
    # We use a client-side callback for speed or just update the URL output
    # But Dash dcc.Location can be updated via callback.
    @app.callback(
        Output('url', 'pathname'),
        Input({'type': 'file-view-btn', 'index': ALL}, 'n_clicks'),
        prevent_initial_call=True
    )
    def navigate_to_file(n_clicks):
        if not ctx.triggered:
            return "/"
            
        # Get the ID of the button that was clicked
        button_id = ctx.triggered_id
        if not button_id:
            return "/"
            
        file_path = button_id['index']
        # URL encode the file path to be safe
        safe_path = urllib.parse.quote(file_path)
        return f"/file/{safe_path}"

    # Update Global Map, Graphs & Stats when Checkboxes change, Focus clicked, or Tab changes
    @app.callback(
        [Output('global-map-graph', 'figure'),
         Output('global-stats-container', 'children')],
        [Input({'type': 'file-check', 'index': ALL}, 'value'),
         Input({'type': 'file-focus-btn', 'index': ALL}, 'n_clicks'),
         Input('global-view-tabs', 'active_tab')],
        State({'type': 'file-check', 'index': ALL}, 'id')
    )
    def update_global_dashboard(checked_values, focus_clicks, active_tab, checked_ids):
        # Determine which files are checked
        selected_files = []
        for val, id_dict in zip(checked_values, checked_ids):
            if val:
                 selected_files.append(id_dict['index'])
        
        # Determine focus
        focus_gps = None
        if ctx.triggered_id and 'type' in ctx.triggered_id and ctx.triggered_id['type'] == 'file-focus-btn':
             focus_gps = ctx.triggered_id['index']
             
        # Prepare summary stats for trace classification (used in both modes)
        summary_stats = service.get_summary_stats(files_filter=selected_files)
        from hfk.Graphic.layout import create_trace_type_cards

        # Map is always updated
        fig_map = visualizer.get_map_figure(focus_gps=focus_gps, files_filter=selected_files, color_phases=False)

        if active_tab == 'summary':
            from hfk.Graphic.layout import create_summary_content
            content = create_summary_content(summary_stats)
        else:
            # Detailed Mode
            # Generate Performance Landscapes
            fig_f_climb = visualizer.get_performance_landscape_figure(files_filter=selected_files, phase_type='flight', metric_type='climb')
            fig_f_desc = visualizer.get_performance_landscape_figure(files_filter=selected_files, phase_type='flight', metric_type='descent')
            
            fig_w_climb = visualizer.get_performance_landscape_figure(files_filter=selected_files, phase_type='walk', metric_type='climb')
            fig_w_desc = visualizer.get_performance_landscape_figure(files_filter=selected_files, phase_type='walk', metric_type='descent')
            
            from hfk.Graphic.layout import create_distance_card
            detailed_stats = service.get_collection_stats(files_filter=selected_files)
            
            # Build the Detailed Layout
            from dash import dcc
            content = html.Div([
                # Row 1: Shared Trace Type Cards
                create_trace_type_cards(summary_stats['counts']),
                
                # Flight Performance Landscape
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([html.I(className="fas fa-paper-plane me-2"), "Flight Performance"], className="text-white bg-info"),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col(create_stats_card("Climb", detailed_stats["flight"]["climb"]["rate"], detailed_stats["flight"]["climb"]["elevation"], unit="m/s"), md=4),
                                    dbc.Col(create_stats_card("Descent", detailed_stats["flight"]["descent"]["rate"], detailed_stats["flight"]["descent"]["elevation"], unit="m/s"), md=4),
                                    dbc.Col(create_distance_card("Total Distance", detailed_stats["flight"]["distance"], icon_class="fas fa-route"), md=4)
                                ], className="mb-3"),
                                # Flight Landscape Graphs (Stacked)
                                dbc.Row([
                                    dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig_f_climb, style={"height": "350px"})), className="shadow-sm mb-3"), width=12),
                                    dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig_f_desc, style={"height": "350px"})), className="shadow-sm"), width=12)
                                ])
                            ])
                        ], className="h-100 shadow-sm")
                    ], width=12)
                ], className="mb-4"),
                
                # Walk Performance Landscape
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([html.I(className="fas fa-hiking me-2"), "Walk Performance"], className="text-white bg-success"),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col(create_stats_card("Climb", detailed_stats["walk"]["climb"]["rate"], detailed_stats["walk"]["climb"]["elevation"], unit="m/h"), md=4),
                                    dbc.Col(create_stats_card("Descent", detailed_stats["walk"]["descent"]["rate"], detailed_stats["walk"]["descent"]["elevation"], unit="m/h"), md=4),
                                    dbc.Col(create_distance_card("Total Distance", detailed_stats["walk"]["distance"], icon_class="fas fa-walking"), md=4)
                                ], className="mb-3"),
                                 # Walk Landscape Graphs (Stacked)
                                dbc.Row([
                                    dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig_w_climb, style={"height": "350px"})), className="shadow-sm mb-3"), width=12),
                                    dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig_w_desc, style={"height": "350px"})), className="shadow-sm"), width=12)
                                ])
                            ])
                        ], className="h-100 shadow-sm")
                    ], width=12)
                ], className="mb-4"),
            ])
        
        return fig_map, content