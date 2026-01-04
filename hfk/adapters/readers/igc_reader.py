# Copyright (C) 2024 aherve4
# Licensed under the GNU GPL v3.0

import os
import datetime
import pandas as pd
from ...ports.reader import TrackReader
from ...domain.models import Track

class IgcReader(TrackReader):
    """Adapter for reading IGC files."""
    
    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith(".igc")

    def read(self, file_path: str) -> Track:
        if not os.access(file_path, os.R_OK):
            raise Exception(f"File {file_path} cannot be read")
            
        lTime = []
        lAltPressure = []
        lAltGps = []
        lLat = []
        fLat = ""
        lLong = []
        fLong = ""

        flight_date = datetime.date.today()

        with open(file_path, "r") as fFile:
            lLines = fFile.readlines()
            # First pass for date
            for line in lLines:
                if line.startswith("HFDTE"):
                    try:
                        date_str = line[5:].strip()
                        if ":" in date_str:
                            date_str = date_str.split(":")[-1].strip()
                        
                        if len(date_str) >= 6:
                            day = int(date_str[0:2])
                            month = int(date_str[2:4])
                            year_short = int(date_str[4:6])
                            year = 2000 + year_short
                            flight_date = datetime.date(year, month, day)
                    except ValueError:
                        pass

                if line.startswith("B"):
                    try:
                        oNewTime = datetime.datetime(
                            flight_date.year, 
                            flight_date.month, 
                            flight_date.day, 
                            int(line[1:3]), 
                            int(line[3:5]), 
                            int(line[5:7])
                        )
                        lTime.append(oNewTime)
                        lAltGps.append(int(line[30:35]))
                        lAltPressure.append(int(line[25:30]))
                        
                        fLat = float(line[7:9]) + float(line[9:11]+"."+line[11:14])/60.
                        if line[14:15] == "S":
                            fLat = -fLat
                        
                        fLong = float(line[15:18]) + float(line[18:20]+"."+line[20:23])/60.
                        if line[23:24] == "W":
                            fLong = -fLong
                            
                        lLat.append(fLat)
                        lLong.append(fLong)
                    except (ValueError, IndexError):
                        continue

        oDf = pd.DataFrame({
            "time": lTime, 
            "Alt_gps": lAltGps,
            "Alt_pressure": lAltPressure, 
            "Lat": lLat, 
            "Long": lLong
        })
        
        oDf.set_index("time", inplace=True)
        oDf.sort_index(inplace=True)
        
        return Track(dataframe=oDf, file_path=file_path)
