import pytest
import pandas as pd
import datetime
from hfk.domain.models import Point, Track, Phase, LogicalPhase
from hfk.domain.analysis_engine import AnalysisEngine

@pytest.fixture
def sample_track_df():
    times = [
        datetime.datetime(2025, 1, 1, 10, 0, 0) + datetime.timedelta(seconds=i*10)
        for i in range(100)
    ]
    # Simple climb then descent
    alts = [500 + i*10 for i in range(50)] + [1000 - i*10 for i in range(50)]
    lats = [42.0 + i*0.0001 for i in range(100)]
    lons = [1.0 + i*0.0001 for i in range(100)]
    
    df = pd.DataFrame({
        "time": times,
        "Alt_gps": alts,
        "Alt_pressure": alts,
        "Lat": lats,
        "Long": lons
    })
    df.set_index("time", inplace=True)
    return df

def test_point_instantiation():
    now = datetime.datetime.now()
    p = Point(now, 42.0, 1.0, 1000.0, 950.0)
    assert p.time == now
    assert p.lat == 42.0
    assert p.lon == 1.0
    assert p.alt_gps == 1000.0
    assert p.alt_pressure == 950.0

def test_track_instantiation(sample_track_df):
    track = Track(dataframe=sample_track_df, file_path="test.igc")
    assert not track.dataframe.empty
    assert track.file_name == "test.igc"
    
def test_track_resampling(sample_track_df):
    track = Track(dataframe=sample_track_df)
    res_df = track.get_resampled("1min")
    assert len(res_df) < len(sample_track_df)

def test_phase_logic(sample_track_df):
    # Test a simple climb phase
    climb_df = sample_track_df.iloc[:50]
    phase = Phase(climb_df, bUp=True)
    assert phase.direction is True
    assert phase.height > 0
    
    phase.compute_distance()
    assert phase.distance > 0
    # In our dummy data, vertical rate will be high enough or speed high enough?
    # 500m in 500s = 3600 m/h -> should be flight if rate > 1000
    assert phase.rate_metersperhour > 1000
    assert phase.is_flight == True

def test_analysis_engine_splitting(sample_track_df):
    track = Track(dataframe=sample_track_df)
    # 10s points, use 10s resample to match
    phases = AnalysisEngine.split_into_phases(track, resample_interval="10s")
    
    print(f"Detected {len(phases)} phases")
    for i, p in enumerate(phases):
        print(f"Phase {i}: direction={p.direction}, is_flight={p.is_flight}, points={len(p.dataframe)}")

    # We expect at least one UP and then some DOWN phases
    assert len(phases) >= 2
    assert phases[0].direction == True
    assert any(p.direction == False for p in phases)

def test_logical_phase_aggregation(sample_track_df):
    track = Track(dataframe=sample_track_df)
    phases = AnalysisEngine.split_into_phases(track, resample_interval="10s")
    logical_phases = AnalysisEngine.get_logical_phases(phases)
    
    assert len(logical_phases) > 0
    # In our data, major phases should be flights
    # We might have a small setup phase that isn't flight
    flight_phases = [lp for lp in logical_phases if lp.is_flight]
    assert len(flight_phases) > 0
    for lp in flight_phases:
        assert not lp.dataframe.empty
