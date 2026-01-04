# Copyright (C) 2024 aherve4
# Licensed under the GNU GPL v3.0

from abc import ABC, abstractmethod
from typing import List
from ..domain.models import Track

class TrackReader(ABC):
    """Port interface for reading track files."""
    
    @abstractmethod
    def read(self, file_path: str) -> Track:
        """Reads a file and returns a standardized Track domain entity."""
        pass

    @abstractmethod
    def can_handle(self, file_path: str) -> bool:
        """Returns True if this reader can handle the given file extension."""
        pass
