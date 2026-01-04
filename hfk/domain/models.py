# Copyright (C) 2024 aherve4
# Licensed under the GNU GPL v3.0

import pandas as pd
import datetime
import logging
import pyproj

class Point:
    """Value object representing a single recording point."""
    def __init__(self, time: datetime.datetime, lat: float, lon: float, alt_gps: float, alt_pressure: float = None):
        self.time = time
        self.lat = lat
        self.lon = lon
        self.alt_gps = alt_gps
        self.alt_pressure = alt_pressure

class Track:
    """Entity representing a full recording."""
    def __init__(self, dataframe: pd.DataFrame, file_path: str = None):
        self.dataframe = dataframe
        self.file_path = file_path
        self.file_name = pd.io.common.os.path.basename(file_path) if file_path else "Unknown"

    def get_resampled(self, interval: str):
        if not interval:
            return self.dataframe
        return self.dataframe.resample(interval).mean()

class Phase:
    """Results of track segmentation (Walk/Flight)."""
    def __init__(self, df: pd.DataFrame, bUp: bool):
        self.dataframe = df
        self.direction = bUp
        self.distance = 0
        
        if self.dataframe.empty:
            self.height = 0
            self.duration = datetime.timedelta(0)
            self.durationHours = 0
            self.rate_metersperhour = 0
            self.is_flight = False
            return

        self.height = (-1 * (not bUp) + 1 * bUp) * (self.dataframe["Alt_gps"].max() - self.dataframe["Alt_gps"].min())
        self.duration = self.dataframe.index.max() - self.dataframe.index.min()
        
        if isinstance(self.duration, datetime.timedelta):
            self.durationHours = self.duration.total_seconds()/3600.0
        else:
            self.durationHours = 0
            
        self.rate_metersperhour = self.height/self.durationHours if self.durationHours != 0 else 0
        
        # Determine if it is a flight phase based on heuristics
        # These will be updated by the AnalysisEngine after calling compute_distance
        self.is_flight = False 
        self.speed_kmh = 0

    def compute_distance(self):
        self.distance = 0
        fLat = None
        fLong = None
        
        lLat = self.dataframe["Lat"].tolist()
        lLong = self.dataframe["Long"].tolist()
        
        for lat, lon in zip(lLat, lLong):
            if fLat is not None and fLong is not None:
                geod = pyproj.Geod(ellps="WGS84")
                _, _, distance = geod.inv(fLong, fLat, lon, lat)
                self.distance += distance
            fLat = lat
            fLong = lon
        
        # Calculate horizontal speed in km/h
        self.speed_kmh = (self.distance / 1000.0) / self.durationHours if self.durationHours > 0 else 0
        
        # Determine activity type
        # speed > 15 km/h OR |vertical rate| > 1000 m/h
        self.is_flight = (self.speed_kmh > 15) or \
                         (abs(self.rate_metersperhour) > 1000)

    def __str__(self):
        dir_str = "UP" if self.direction else "DOWN"
        if self.dataframe.empty:
            return f"Phase {dir_str} : [EMPTY]"
        return f"Phase {dir_str} : {self.dataframe.index[0]} -> {self.dataframe.index[-1]} | Height: {self.height}m"

class LogicalPhase:
    """Aggregated segments of the same activity type."""
    def __init__(self, phases: list):
        if not phases:
            raise ValueError("LogicalPhase requires at least one phase")
            
        self.phases = phases
        self.is_flight = getattr(phases[0], 'is_flight', False)
        
        # Merge dataframes
        self.dataframe = pd.concat([p.dataframe for p in phases])
        self.dataframe = self.dataframe[~self.dataframe.index.duplicated(keep='first')].sort_index()
        
        # Combined stats
        self.distance = sum(p.distance for p in phases)
        self.duration = self.dataframe.index.max() - self.dataframe.index.min()
        self.durationHours = self.duration.total_seconds() / 3600.0 if self.duration.total_seconds() > 0 else 0
        
        self.d_plus = sum(p.height for p in phases if p.height > 0)
        self.d_minus = sum(abs(p.height) for p in phases if p.height < 0)
        
        self.min_alt = round(self.dataframe["Alt_gps"].min(), 1)
        self.max_alt = round(self.dataframe["Alt_gps"].max(), 1)
        
        self.start_time = self.dataframe.index.min().strftime("%H:%M:%S")
        self.end_time = self.dataframe.index.max().strftime("%H:%M:%S")
        
        # Rate stats
        climb_rates = [p.rate_metersperhour for p in phases if p.rate_metersperhour > 0]
        descent_rates = [abs(p.rate_metersperhour) for p in phases if p.rate_metersperhour < 0]
        
        def get_avg_rate(rates, is_flight):
            if not rates: return 0
            avg_r = sum(rates) / len(rates)
            if is_flight:
                avg_r = avg_r / 3600.0 # Convert to m/s for flight
            return round(avg_r, 2)

        self.climb_rate_val = get_avg_rate(climb_rates, self.is_flight)
        self.descent_rate_val = get_avg_rate(descent_rates, self.is_flight)
        
        self.climb_rate = str(self.climb_rate_val)
        self.descent_rate = str(self.descent_rate_val)
        
        # Icon/Title for UI
        self.icon = "fas fa-paper-plane" if self.is_flight else "fas fa-walking"
        self.type_label = "Flight" if self.is_flight else "Walk"
