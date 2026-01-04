import pytest
import os
from hfk.adapters.readers.igc_reader import IgcReader
from hfk.domain.models import Track

@pytest.fixture
def reader():
    return IgcReader()

@pytest.fixture
def test_data_path():
    return "Tests/Data"

def test_reader_can_handle(reader):
    assert reader.can_handle("test.igc") == True
    assert reader.can_handle("test.IGC") == True
    assert reader.can_handle("test.txt") == False

def test_reader_read_track1(reader, test_data_path):
    path = os.path.join(test_data_path, "track1.igc")
    if not os.path.exists(path):
        pytest.skip("Test file not found")
        
    track = reader.read(path)
    assert isinstance(track, Track)
    assert not track.dataframe.empty
    assert "Alt_gps" in track.dataframe.columns
    assert "Lat" in track.dataframe.columns
    assert "Long" in track.dataframe.columns

def test_reader_read_track2(reader, test_data_path):
    path = os.path.join(test_data_path, "track2.igc")
    if not os.path.exists(path):
        pytest.skip("Test file not found")
        
    track = reader.read(path)
    assert isinstance(track, Track)
    assert not track.dataframe.empty

def test_reader_invalid_file(reader):
    with pytest.raises(Exception):
        reader.read("non_existent.igc")

def test_reader_empty_file(reader):
    path = os.path.join("Tests/EdgeCases", "empty.igc")
    track = reader.read(path)
    assert track.dataframe.empty

def test_reader_headers_only_file(reader):
    path = os.path.join("Tests/EdgeCases", "headers_only.igc")
    track = reader.read(path)
    assert track.dataframe.empty
