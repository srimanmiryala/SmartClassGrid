from typing import List, Dict, Optional, Tuple
import heapq
from src.models.course import Course
from src.models.room import Room
from src.models.faculty import Faculty
from src.models.schedule import Schedule, ScheduleEntry

class GreedyScheduler:
    """Greedy algorithm for initial schedule generation."""
    
    def __init__(self, courses: List[Course], rooms: List[Room], faculty: List[Faculty]):
        self.courses = courses
        self.rooms = rooms
        self.faculty = faculty
        self.faculty_dict = {f.id: f for f in faculty}
        self.room_dict = {r.id: r for r in rooms}
        
        # Time slots
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.times = ['08:00', '09:00', '10:00', '11:00', '12:00', 
                     '13:00', '14:00', '15:00', '16:00', '17:00']
    
    def generate_schedule(self) -> Schedule:
        """Generate initial schedule using greedy approach."""
        schedule = Schedule()
        
        # Sort courses by priority (constraints, difficulty, etc.)
        prioritized_courses = self._prioritize_courses()
        
        for course in prioritized_courses:
            best_assignment = self._find_best_assignment(course, schedule)
            
            if best_assignment:
                entry = self._create_schedule_entry(course, best_assignment)
                schedule.add_entry(entry)
                self._update_availability(best_assignment)
            else:
                schedule.conflicts.append(f"Could not schedule course {course.code}")
        
        schedule.calculate_metrics()
        return schedule
    
    def _prioritize_courses(self) -> List[Course]:
        """Prioritize courses based on constraints and difficulty."""
        priority_queue = []
        
        for course in self.courses:
            # Calculate priority score (higher = more difficult to schedule)
            priority = 0
            
            # Lab courses are harder to schedule
            if course.course_type.value == "lab":
                priority += 10
            
            # Courses with equipment requirements
            priority += len(course.required_equipment) * 2
            
            # Large capacity courses
            if course.capacity > 100:
                priority += 5
            
            # Courses with specific time preferences
            if course.preferred_times:
                priority += 3
            
            # Consecutive hour requirements
            if course.consecutive_hours:
                priority += 4
            
            heapq.heappush(priority_queue, (-priority, course))
        
        return [course for _, course in priority_queue]
    
    def _find_best_assignment(self, course: Course, current_schedule: Schedule) -> Optional[Dict]:
        """Find the best room-time assignment for a course."""
        best_assignment = None
        best_score = -1
        
        for day in self.days:
            for time in self.times:
                for room in self.rooms:
                    assignment = {
                        'day': day,
                        'time': time,
                        'room': room,
                        'faculty': self.faculty_dict[course.faculty_id],
                        'duration': course.duration
                    }
                    
                    if self._is_valid_assignment(assignment, course, current_schedule):
                        score = self._calculate_assignment_score(assignment, course)
                        
                        if score > best_score:
                            best_score = score
                            best_assignment = assignment
        
        return best_assignment
    
    def _is_valid_assignment(self, assignment: Dict, course: Course, 
                           current_schedule: Schedule) -> bool:
        """Check if assignment is valid (hard constraints)."""
        room = assignment['room']
        faculty = assignment['faculty']
        day = assignment['day']
        time = assignment['time']
        duration = assignment['duration']
        
        # Check room capacity
        if room.capacity < course.capacity:
            return False
        
        # Check room type compatibility
        if course.room_type_required and room.room_type.value != course.room_type_required:
            return False
        
        # Check required equipment
        for equipment in course.required_equipment:
            if equipment not in room.equipment:
                return False
        
        # Check room availability
        if not room.is_available(day, time, duration):
            return False
        
        # Check faculty availability
        if not faculty.is_available(day, time, duration):
            return False
        
        return True
    
    def _calculate_assignment_score(self, assignment: Dict, course: Course) -> float:
        """Calculate quality score for an assignment."""
        room = assignment['room']
        faculty = assignment['faculty']
        day = assignment['day']
        time = assignment['time']
        
        score = 1.0
        
        # Course preference score
        score *= course.get_constraint_score(day, time, room.id)
        
        # Faculty preference score
        score *= faculty.get_preference_score(day, time)
        
        # Room efficiency (prefer rooms closer to course capacity)
        capacity_ratio = course.capacity / room.capacity
        if 0.7 <= capacity_ratio <= 1.0:
            score *= 1.2
        elif capacity_ratio < 0.5:
            score *= 0.8
        
        # Room quality bonus
        room_quality = (room.acoustics_rating + room.lighting_rating) / 2
        score *= room_quality
        
        return score
    
    def _create_schedule_entry(self, course: Course, assignment: Dict) -> ScheduleEntry:
        """Create a schedule entry from assignment."""
        entry = ScheduleEntry(
            course=course,
            room=assignment['room'],
            faculty=assignment['faculty'],
            day=assignment['day'],
            time=assignment['time'],
            duration=assignment['duration']
        )
        
        # Calculate quality metrics
        entry.preference_score = self._calculate_assignment_score(assignment, course)
        entry.resource_efficiency = course.capacity / assignment['room'].capacity
        
        return entry
    
    def _update_availability(self, assignment: Dict):
        """Update room and faculty availability after assignment."""
        room = assignment['room']
        faculty = assignment['faculty']
        day = assignment['day']
        time = assignment['time']
        duration = assignment['duration']
        
        room.reserve_slot(day, time, duration)
        faculty.assign_slot(day, time, duration)

