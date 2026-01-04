# Copyright (C) 2024 aherve4
# Licensed under the GNU GPL v3.0

import logging
import pyproj
import pandas as pd
from .models import Track, Phase, LogicalPhase

class AnalysisEngine:
    """Core domain service for analyzing tracks and detecting phases."""
    
    THRESHOLD_CHANGE_STATE = 10 # confirmation window in samples
    ALTITUDE_HYSTERESIS_MARGIN = 10 # meters
    
    @staticmethod
    def split_into_phases(track: Track, resample_interval: str = "1min") -> list:
        """Segments a track into activity phases (Walk/Flight, Up/Down)."""
        geod = pyproj.Geod(ellps="WGS84")
        altitude_col = "Alt_gps"
        
        df_resampled = track.get_resampled(resample_interval)
        if df_resampled.empty:
            return []
            
        df_full = track.dataframe

        # 1. Pre-calculate activity triggers (Speed & Vertical Rate)
        lActivity = [] # True for Flight, False for Walk
        for k in range(len(df_resampled)):
            if k == 0:
                lActivity.append(False)
                continue
                
            p1 = df_resampled.iloc[k-1]
            p2 = df_resampled.iloc[k]
            
            # Ground Speed
            _, _, dist = geod.inv(p1["Long"], p1["Lat"], p2["Long"], p2["Lat"])
            dt = (df_resampled.index[k] - df_resampled.index[k-1]).total_seconds() / 3600.0
            speed = (dist / 1000.0) / dt if dt > 0 else 0
            
            # Vertical Rate
            rate = (p2[altitude_col] - p1[altitude_col]) / dt if dt > 0 else 0
            
            # Flight criteria: Speed > 15 km/h OR |rate| > 1000 m/h
            is_f = (speed > 15) or (abs(rate) > 1000)
            lActivity.append(is_f)

        # 2. Main splitting logic: Direction + Activity Trigger
        if len(df_resampled) >= 2:
            bUp = df_resampled[altitude_col].iloc[1] >= df_resampled[altitude_col].iloc[0]
        else:
            bUp = True
            
        bFlight = lActivity[0]
        
        phases = []
        current_phase_time = []
        change_state_time = []
        extreme_altitude = df_resampled[altitude_col].iloc[0]
        it_change_state = 0
        
        for k, time_idx in enumerate(df_resampled.index):
            current_alt = df_resampled[altitude_col][time_idx]
            current_is_f = lActivity[k]
            
            activity_aligned = (current_is_f == bFlight)
            
            direction_aligned = False
            if bUp:
                if current_alt >= extreme_altitude - AnalysisEngine.ALTITUDE_HYSTERESIS_MARGIN:
                    direction_aligned = True
                    if current_alt > extreme_altitude: extreme_altitude = current_alt
            else:
                if current_alt <= extreme_altitude + AnalysisEngine.ALTITUDE_HYSTERESIS_MARGIN:
                    direction_aligned = True
                    if current_alt < extreme_altitude: extreme_altitude = current_alt
            
            if activity_aligned and direction_aligned:
                if it_change_state > 0:
                    current_phase_time += change_state_time
                    change_state_time = []
                    it_change_state = 0
                current_phase_time.append(time_idx)
            else:
                it_change_state += 1
                change_state_time.append(time_idx)
                
                if it_change_state >= AnalysisEngine.THRESHOLD_CHANGE_STATE:
                    # Finalize phase
                    if current_phase_time:
                         start_t = current_phase_time[0]
                         end_t = current_phase_time[-1]
                         phase_slice = df_full.loc[start_t:end_t].copy()
                         if not phase_slice.empty:
                             p = Phase(phase_slice, bUp)
                             p.compute_distance()
                             phases.append(p)
                    
                    # Reset state
                    current_phase_time = change_state_time
                    change_state_time = []
                    it_change_state = 0
                    bUp = not bUp if not direction_aligned else bUp
                    bFlight = current_is_f
                    extreme_altitude = current_alt
                    
        # Add last remaining phase
        if current_phase_time:
             current_phase_time += change_state_time
             start_t = current_phase_time[0]
             end_t = current_phase_time[-1]
             phase_slice = df_full.loc[start_t:end_t].copy()
             if not phase_slice.empty:
                 p = Phase(phase_slice, bUp)
                 p.compute_distance()
                 phases.append(p)
            
        return phases

    @staticmethod
    def get_logical_phases(phases: list) -> list:
        """Groups consecutive phases of the same activity type."""
        if not phases:
            return []
            
        logical_phases = []
        current_group = [phases[0]]
        current_is_f = getattr(phases[0], 'is_flight', False)
        
        for p in phases[1:]:
            p_is_f = getattr(p, 'is_flight', False)
            if p_is_f == current_is_f:
                current_group.append(p)
            else:
                logical_phases.append(LogicalPhase(current_group))
                current_group = [p]
                current_is_f = p_is_f
        
        if current_group:
            logical_phases.append(LogicalPhase(current_group))
            
        return logical_phases
