#! /usr/bin/env python

# IGC format information
# https://xp-soaring.github.io/igc_file_format/igc_format_2008.html#link_preface

# Modules imports
import plotly.express as px
import argparse
import logging

# Project imports

# Input arguments
parser = argparse.ArgumentParser(description='Perform an analysis of a set of IGC files.')
# # Cannot use folder and file together
# group = parser.add_mutually_exclusive_group()
# group.add_argument("-d", '--folder', nargs='+', help='provide one (or several) folder(s) to analyze')
# group.add_argument("-f", '--file', nargs='+', help='provide one (or several) igc file(s)')
parser.add_argument("target", nargs='+', help='provide path(s) to igc file(s) or to folder(s) containing igc file(s)')
# enables the use of 'IGCAnalyser --verbose' (no trailing value provided)
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
# parser.add_argument("-c", "--cli", help="cli mode",
#                     action="store_true")
args = parser.parse_args()

if args.verbose:
    logging.basicConfig(level=logging.DEBUG)
    logging.debug(f"args = {args}")
    logging.debug(f"args.target = {args.target}")

if args.target:
    from hfk import TrackCollection
    from hfk.adapters.visualizers.dash_visualizer import DashVisualizer

    service = TrackCollection(args.target)
    visualizer = DashVisualizer(service)
    
    logging.debug(f"Files found : {list(service.tracks.keys())}")
    
    from dash import Dash
    import dash_bootstrap_components as dbc
    from hfk.Graphic.layout import create_layout
    from hfk.controller.callbacks import register_callbacks

    app = Dash(__name__, external_stylesheets=[dbc.themes.LUX, "https://use.fontawesome.com/releases/v5.15.4/css/all.css"], suppress_callback_exceptions=True)

    # Initialise dashboard layout
    app.layout = create_layout(service, visualizer)

    # Records callbacks
    register_callbacks(app, service, visualizer)

    if __name__ == '__main__':
        app.run_server(debug=True)