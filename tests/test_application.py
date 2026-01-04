import pytest
import os
import pandas as pd
import datetime
from hfk.application.collection_service import TrackCollectionService
from hfk.adapters.readers.igc_reader import IgcReader

@pytest.fixture
def service():
    # Use real IgcReader since it's an integration-ish test for service
    return TrackCollectionService(readers=[IgcReader()])

@pytest.fixture
def test_data_path():
    return os.path.abspath("tests/Data")

def test_service_load_files(service, test_data_path):
    # Tests loading the anonymized files
    print(test_data_path)    
    service.load_files(test_data_path)
    assert len(service.tracks) >= 2
    
    # Check if colors are assigned
    for path in service.tracks:
        assert service.get_file_color(path) is not None

def test_service_get_collection_stats(service, test_data_path):
    service.load_files(test_data_path)
    stats = service.get_collection_stats()
    
    assert "flight" in stats
    assert "walk" in stats
    assert "distance" in stats["flight"]
    assert stats["flight"]["distance"]["avg"] > 0

def test_service_filtering(service, test_data_path):
    service.load_files(test_data_path)
    all_paths = list(service.tracks.keys())
    
    # Filter for only the first file
    target_path = all_paths[0]
    stats = service.get_collection_stats(files_filter=[target_path])
    
    # How to verify? Summary stats should only count one file
    summary = service.get_summary_stats(files_filter=[target_path])
    assert summary["counts"]["total"] == 1

def test_service_get_global_stats(service, test_data_path):
    service.load_files(test_data_path)
    path = list(service.tracks.keys())[0]
    
    stats = service.get_global_stats(path)
    assert "total_dist" in stats
    assert "flight_phases" in stats
    assert "walk_phases" in stats
