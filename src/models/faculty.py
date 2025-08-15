from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Faculty:
    """Represents a faculty member with preferences and constraints."""
    
    id: str
    name: str
    department: str
    email: str
    
    # Teaching constraints
    max_teaching_hours: int = 20
    preferred_days: List[str] = None
    preferred_times: List[str] = None
    unavailable_slots: Dict[str, List[str]] = None
    
    # Preferences
    consecutive_classes_preference: bool = True
    break_duration_required: int = 1  # hours between classes
    
    # Current schedule tracking
    current_teaching_hours: int = 0
    assigned_slots: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.preferred_days is None:
            self.preferred_days = []
        if self.preferred_times is None:
            self.preferred_times = []
        if self.unavailable_slots is None:
            self.unavailable_slots = {}
        if self.assigned_slots is None:
            self.assigned_slots = {}
    
    def is_available(self, day: str, time: str, duration: int = 1) -> bool:
        """Check if faculty is available for specified time slot."""
        # Check unavailable slots
        if day in self.unavailable_slots and time in self.unavailable_slots[day]:
            return False
        
        # Check if already assigned
        if day in self.assigned_slots and time in self.assigned_slots[day]:
            return False
        
        # Check teaching hours limit
        if self.current_teaching_hours + duration > self.max_teaching_hours:
            return False
        
        return True
    
    def assign_slot(self, day: str, time: str, duration: int = 1):
        """Assign time slot to faculty."""
        if day not in self.assigned_slots:
            self.assigned_slots[day] = []
        
        # Add all hours for the duration
        times = ['08:00', '09:00', '10:00', '11:00', '12:00', 
                '13:00', '14:00', '15:00', '16:00', '17:00']
        start_idx = times.index(time)
        
        for i in range(duration):
            if start_idx + i < len(times):
                assign_time = times[start_idx + i]
                self.assigned_slots[day].append(assign_time)
        
        self.current_teaching_hours += duration
    
    def get_preference_score(self, day: str, time: str) -> float:
        """Calculate preference score for given time slot."""
        score = 1.0
        
        if self.preferred_days and day in self.preferred_days:
            score *= 1.2
        
        if self.preferred_times and time in self.preferred_times:
            score *= 1.2
        
        return min(score, 2.0)  # Cap at 2.0

