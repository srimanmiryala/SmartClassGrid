from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from .course import Course
from .room import Room
from .faculty import Faculty

@dataclass
class ScheduleEntry:
    """Single schedule entry representing a class assignment."""
    
    course: Course
    room: Room
    faculty: Faculty
    day: str
    time: str
    duration: int
    
    # Quality metrics
    conflict_score: float = 0.0
    preference_score: float = 1.0
    resource_efficiency: float = 1.0

@dataclass
class Schedule:
    """Complete schedule with all assignments and metrics."""
    
    entries: List[ScheduleEntry] = None
    conflicts: List[str] = None
    
    # Performance metrics
    total_conflicts: int = 0
    accuracy_score: float = 0.0
    room_utilization: float = 0.0
    faculty_satisfaction: float = 0.0
    
    def __post_init__(self):
        if self.entries is None:
            self.entries = []
        if self.conflicts is None:
            self.conflicts = []
    
    def add_entry(self, entry: ScheduleEntry):
        """Add a schedule entry."""
        self.entries.append(entry)
    
    def remove_entry(self, entry: ScheduleEntry):
        """Remove a schedule entry."""
        if entry in self.entries:
            self.entries.remove(entry)
    
    def get_schedule_matrix(self) -> Dict[str, Dict[str, List[ScheduleEntry]]]:
        """Get schedule organized by day and time."""
        matrix = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        times = ['08:00', '09:00', '10:00', '11:00', '12:00', 
                '13:00', '14:00', '15:00', '16:00', '17:00']
        
        for day in days:
            matrix[day] = {time: [] for time in times}
        
        for entry in self.entries:
            if entry.day in matrix and entry.time in matrix[entry.day]:
                matrix[entry.day][entry.time].append(entry)
        
        return matrix
    
    def calculate_metrics(self):
        """Calculate schedule quality metrics."""
        if not self.entries:
            return
        
        # Calculate conflicts
        self.total_conflicts = len(self.conflicts)
        
        # Calculate accuracy (percentage of successful assignments)
        total_possible = len(self.entries)
        successful = total_possible - self.total_conflicts
        self.accuracy_score = (successful / total_possible) * 100 if total_possible > 0 else 0
        
        # Calculate average preference score
        if self.entries:
            avg_preference = sum(entry.preference_score for entry in self.entries) / len(self.entries)
            self.faculty_satisfaction = avg_preference * 100
        
        # Room utilization calculated separately by ResourceOptimizer
    
    def get_conflicts_by_type(self) -> Dict[str, int]:
        """Categorize conflicts by type."""
        conflict_types = {
            'room_double_booking': 0,
            'faculty_double_booking': 0,
            'capacity_exceeded': 0,
            'equipment_missing': 0,
            'time_constraint_violation': 0
        }
        
        for conflict in self.conflicts:
            if 'room' in conflict.lower() and 'double' in conflict.lower():
                conflict_types['room_double_booking'] += 1
            elif 'faculty' in conflict.lower() and 'double' in conflict.lower():
                conflict_types['faculty_double_booking'] += 1
            elif 'capacity' in conflict.lower():
                conflict_types['capacity_exceeded'] += 1
            elif 'equipment' in conflict.lower():
                conflict_types['equipment_missing'] += 1
            else:
                conflict_types['time_constraint_violation'] += 1
        
        return conflict_types

