from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

class RoomType(Enum):
    CLASSROOM = "classroom"
    LAB = "lab"
    AUDITORIUM = "auditorium"
    SEMINAR_ROOM = "seminar_room"
    COMPUTER_LAB = "computer_lab"

@dataclass
class Room:
    """Represents a room with its capacity and equipment."""
    
    id: str
    name: str
    capacity: int
    room_type: RoomType
    building: str
    floor: int
    
    # Equipment and features
    equipment: List[str] = None
    features: List[str] = None
    
    # Availability (True = available, False = occupied)
    availability: Dict[str, Dict[str, bool]] = None
    
    # Room quality metrics
    acoustics_rating: float = 1.0
    lighting_rating: float = 1.0
    accessibility_rating: float = 1.0
    
    def __post_init__(self):
        if self.equipment is None:
            self.equipment = []
        if self.features is None:
            self.features = []
        if self.availability is None:
            # Initialize with all slots available
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            times = ['08:00', '09:00', '10:00', '11:00', '12:00', 
                    '13:00', '14:00', '15:00', '16:00', '17:00']
            self.availability = {
                day: {time: True for time in times} for day in days
            }
    
    def is_available(self, day: str, time: str, duration: int = 1) -> bool:
        """Check if room is available for specified time slot."""
        if day not in self.availability:
            return False
        
        times = list(self.availability[day].keys())
        if time not in times:
            return False
        
        start_idx = times.index(time)
        for i in range(duration):
            if start_idx + i >= len(times):
                return False
            check_time = times[start_idx + i]
            if not self.availability[day][check_time]:
                return False
        
        return True
    
    def reserve_slot(self, day: str, time: str, duration: int = 1):
        """Reserve room for specified time slot."""
        times = list(self.availability[day].keys())
        start_idx = times.index(time)
        for i in range(duration):
            if start_idx + i < len(times):
                reserve_time = times[start_idx + i]
                self.availability[day][reserve_time] = False
    
    def get_utilization_rate(self) -> float:
        """Calculate room utilization percentage."""
        total_slots = sum(len(day_schedule) for day_schedule in self.availability.values())
        occupied_slots = sum(
            sum(1 for available in day_schedule.values() if not available)
            for day_schedule in self.availability.values()
        )
        return (occupied_slots / total_slots) * 100 if total_slots > 0 else 0

