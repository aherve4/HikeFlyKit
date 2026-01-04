# Copyright (C) 2024 aherve4
# Licensed under the GNU GPL v3.0

# HikeFlyKit (hfk) - Simplified API Entry Point

from .adapters.readers.igc_reader import IgcReader
from .application.collection_service import TrackCollectionService

class TrackCollection(TrackCollectionService):
    """
    Simplified entry point for HikeFlyKit.
    
    Automatically initializes with default readers and supports loading
    files directly during instantiation.
    """
    def __init__(self, targets=None):
        # Default readers (currently only IGC, but easy to add more)
        default_readers = [IgcReader()]
        super().__init__(default_readers)
        
        if targets:
            self.load_files(targets)

# Public API
__all__ = ['TrackCollection']
