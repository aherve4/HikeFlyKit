# Copyright (C) 2024 aherve4
# Licensed under the GNU GPL v3.0

import os
import logging
import glob
from typing import List, Dict, Union
import plotly.colors

from ..ports.reader import TrackReader
from ..domain.models import Track, Phase, LogicalPhase
from ..domain.analysis_engine import AnalysisEngine

class TrackCollectionService:
    """Application service to manage and analyze a collection of tracks."""
    
    def __init__(self, readers: List[TrackReader]):
        self.readers = readers
        self.tracks: Dict[str, Track] = {}
        self.phases: Dict[str, List[Phase]] = {}
        self.file_colors: Dict[str, str] = {}
        self.palette = plotly.colors.qualitative.Plotly + plotly.colors.qualitative.Dark24

    def load_files(self, targets: Union[str, List[str]]):
        """Discovers and loads files into the collection."""
        if isinstance(targets, str):
            targets = [targets]
            
        all_paths = self._discover_files(targets)
        for path in all_paths:
            self.add_file(path)

    def _discover_files(self, list_paths: List[str]) -> List[str]:
        paths_to_return = []
        for element in list_paths:
            element_path = os.path.abspath(element)
            if os.path.isfile(element_path):
                paths_to_return.append(element_path)
            elif os.path.isdir(element_path):
                # Search for all supported extensions
                # For now just .igc, but easily extensible
                path_to_search = element_path + "/**/*.igc"
                files = glob.glob(path_to_search, recursive=True)
                paths_to_return += files
        return paths_to_return

    def add_file(self, file_path: str):
        """Processes a single file using the appropriate reader."""
        if file_path in self.tracks:
            return

        for reader in self.readers:
            if reader.can_handle(file_path):
                try:
                    track = reader.read(file_path)
                    self.tracks[file_path] = track
                    
                    # Run analysis immediately
                    phases = AnalysisEngine.split_into_phases(track)
                    self.phases[file_path] = phases
                    
                    # Assign persistent color
                    idx = len(self.file_colors)
                    self.file_colors[file_path] = self.palette[idx % len(self.palette)]
                    
                    logging.info(f"Successfully loaded and analyzed: {file_path}")
                    return
                except Exception as e:
                    logging.error(f"Error processing {file_path} with {reader.__class__.__name__}: {e}")
                    return
        
        logging.warning(f"No suitable reader found for: {file_path}")

    def get_track(self, file_path: str) -> Track:
        return self.tracks.get(file_path)

    def get_phases(self, file_path: str) -> List[Phase]:
        return self.phases.get(file_path, [])

    def get_logical_phases(self, file_path: str) -> List[LogicalPhase]:
        phases = self.get_phases(file_path)
        return AnalysisEngine.get_logical_phases(phases)

    def get_file_color(self, file_path: str) -> str:
        return self.file_colors.get(file_path, "#000000")

    def get_global_stats(self, file_path: str) -> dict:
        """Calculates global stats for a specific track"""
        track = self.get_track(file_path)
        phases = self.get_phases(file_path)
        if not track or not phases:
            return {}

        df = track.dataframe
        duration = df.index.max() - df.index.min()
        max_alt = df['Alt_gps'].max()
        min_alt = df['Alt_gps'].min()
        
        total_climb = sum(p.height for p in phases if p.height > 0)
        total_descent = sum(abs(p.height) for p in phases if p.height < 0)
        total_dist = sum(p.distance for p in phases)

        flight_stats = self._init_group_stats()
        walk_stats = self._init_group_stats()
        
        for phase in phases:
            target = flight_stats if phase.is_flight else walk_stats
            target["count"] += 1
            if phase.height > 0:
                target["up_count"] += 1
                target["total_climb"] += phase.height
                target["climb_rates"].append(phase.rate_metersperhour)
            else:
                target["down_count"] += 1
                target["total_descent"] += abs(phase.height)
                target["descent_rates"].append(phase.rate_metersperhour)
                
            p_min = phase.dataframe['Alt_gps'].min()
            p_max = phase.dataframe['Alt_gps'].max()
            target["alt_min"] = min(target["alt_min"], p_min)
            target["alt_max"] = max(target["alt_max"], p_max)

        return {
            "duration": str(duration).split('.')[0],
            "max_alt": round(max_alt, 1),
            "min_alt": round(min_alt, 1),
            "total_dist": round(total_dist/1000, 2),
            "total_climb": round(total_climb, 0),
            "total_descent": round(total_descent, 0),
            "date": df.index.min().strftime("%Y-%m-%d"),
            "start_time": df.index.min().strftime("%H:%M:%S"),
            "end_time": df.index.max().strftime("%H:%M:%S"),
            "flight_phases": self._finalize_group_stats(flight_stats),
            "walk_phases": self._finalize_group_stats(walk_stats)
        }

    def _init_group_stats(self):
        return {
            "count": 0, "up_count": 0, "down_count": 0, 
            "total_climb": 0, "total_descent": 0, 
            "climb_rates": [], "descent_rates": [], 
            "alt_min": float('inf'), "alt_max": float('-inf')
        }

    def _finalize_group_stats(self, group):
        if group["count"] == 0:
            return {"count": 0, "up_count": 0, "down_count": 0, "climb_range": [0, 0], "descent_range": [0, 0], "alt_range": [0, 0], "total_climb": 0, "total_descent": 0}
        
        get_range = lambda vals: [round(min(vals), 1), round(max(vals), 1)] if vals else [0, 0]
        
        return {
            "count": group["count"],
            "up_count": group["up_count"],
            "down_count": group["down_count"],
            "climb_range": get_range(group["climb_rates"]),
            "descent_range": get_range(group["descent_rates"]),
            "alt_range": [round(group["alt_min"], 1), round(group["alt_max"], 1)],
            "total_climb": round(group["total_climb"], 0),
            "total_descent": round(group["total_descent"], 0)
        }

    def get_collection_stats(self, files_filter=None):
        """Aggregates stats across the collection."""
        data = {
            "walk": {"climb": {"rate": [], "elevation": []}, "descent": {"rate": [], "elevation": []}, "file_distances": []},
            "flight": {"climb": {"rate": [], "elevation": []}, "descent": {"rate": [], "elevation": []}, "file_distances": []}
        }

        selected_files = 0
        for path, track in self.tracks.items():
            if files_filter is not None and path not in files_filter:
                continue
            
            selected_files += 1
            f_dist, w_dist = 0, 0
            
            for phase in self.phases[path]:
                is_f = phase.is_flight
                cat = "flight" if is_f else "walk"
                direction = "climb" if phase.rate_metersperhour > 0 else "descent"
                
                display_rate = abs(phase.rate_metersperhour / 3600.0 if is_f else phase.rate_metersperhour)
                
                data[cat][direction]["rate"].append(display_rate)
                data[cat][direction]["elevation"].append(abs(phase.height))
                
                if is_f: f_dist += phase.distance
                else: w_dist += phase.distance
            
            data["flight"]["file_distances"].append(f_dist / 1000.0)
            data["walk"]["file_distances"].append(w_dist / 1000.0)

        def compute(vals):
            return {"min": round(min(vals), 2), "avg": round(sum(vals)/len(vals), 2), "max": round(max(vals), 2)} if vals else {"min": 0, "avg": 0, "max": 0}

        return {
            "total_files": selected_files,
            "walk": {
                "climb": {"rate": compute(data["walk"]["climb"]["rate"]), "elevation": compute(data["walk"]["climb"]["elevation"])},
                "descent": {"rate": compute(data["walk"]["descent"]["rate"]), "elevation": compute(data["walk"]["descent"]["elevation"])},
                "distance": compute(data["walk"]["file_distances"])
            },
            "flight": {
                "climb": {"rate": compute(data["flight"]["climb"]["rate"]), "elevation": compute(data["flight"]["climb"]["elevation"])},
                "descent": {"rate": compute(data["flight"]["descent"]["rate"]), "elevation": compute(data["flight"]["descent"]["elevation"])},
                "distance": compute(data["flight"]["file_distances"])
            }
        }

    def get_summary_stats(self, files_filter=None):
        """Calculates high-level summary metrics."""
        counts = {"total": 0, "hike_and_fly": 0, "fly_only": 0, "walk_only": 0}
        metrics = {k: [] for k in ["walk_dist", "walk_duration_min", "fly_dist", "walk_climb_rate", "walk_d_plus", "fly_duration_min", "fly_d_plus", "fly_d_minus"]}

        for path, track in self.tracks.items():
            if files_filter is not None and path not in files_filter:
                continue
            
            counts["total"] += 1
            phases = self.phases[path]
            has_f = any(p.is_flight for p in phases)
            has_w = any(not p.is_flight for p in phases)
            
            if has_f and has_w: counts["hike_and_fly"] += 1
            elif has_f: counts["fly_only"] += 1
            elif has_w: counts["walk_only"] += 1
            
            w_dist, w_dur, f_dist, f_dur, w_dp, f_dp, f_dm = 0, 0, 0, 0, 0, 0, 0
            w_rates = []

            for p in phases:
                if p.is_flight:
                    f_dist += p.distance
                    if p.height > 0: f_dp += p.height
                    else: f_dm += abs(p.height)
                    f_dur += p.duration.total_seconds()
                else:
                    w_dist += p.distance
                    w_dur += p.duration.total_seconds()
                    if p.height > 0: 
                        w_dp += p.height
                        w_rates.append(p.rate_metersperhour)

            if has_w:
                metrics["walk_dist"].append(w_dist / 1000.0)
                metrics["walk_duration_min"].append(w_dur / 60.0)
                metrics["walk_d_plus"].append(w_dp)
                if w_rates: metrics["walk_climb_rate"].append(sum(w_rates) / len(w_rates))
            
            if has_f:
                metrics["fly_dist"].append(f_dist / 1000.0)
                metrics["fly_duration_min"].append(f_dur / 60.0)
                metrics["fly_d_plus"].append(f_dp)
                metrics["fly_d_minus"].append(f_dm)

        avg = lambda lst: round(sum(lst) / len(lst), 1) if lst else 0
        return {
            "counts": counts,
            "averages": {k: avg(metrics[k]) for k in metrics}
        }
