from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class CourseType(Enum):
    LECTURE = "lecture"
    LAB = "lab"
    SEMINAR = "seminar"
    TUTORIAL = "tutorial"

@dataclass
class Course:
    """Represents a course with all its constraints and requirements."""
    
    id: str
    name: str
    code: str
    duration: int  # in hours
    course_type: CourseType
    capacity: int
    faculty_id: str
    department: str
    semester: int
    credits: int
    
    # Constraints
    preferred_days: List[str] = None
    preferred_times: List[str] = None
    required_equipment: List[str] = None
    room_type_required: str = None
    consecutive_hours: bool = False
    
    # Preferences (soft constraints)
    faculty_preference_score: float = 1.0
    room_preference_score: float = 1.0
    time_preference_score: float = 1.0
    
    def __post_init__(self):
        if self.preferred_days is None:
            self.preferred_days = []
        if self.preferred_times is None:
            self.preferred_times = []
        if self.required_equipment is None:
            self.required_equipment = []
    
    def get_constraint_score(self, day: str, time: str, room_id: str) -> float:
        """Calculate how well this assignment matches course preferences."""
        score = 1.0
        
        if self.preferred_days and day not in self.preferred_days:
            score *= 0.7
        
        if self.preferred_times and time not in self.preferred_times:
            score *= 0.8
            
        return score

