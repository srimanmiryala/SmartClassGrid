from typing import List, Dict, Optional, Set, Tuple
from copy import deepcopy
from ..models.course import Course
from ..models.room import Room
from ..models.faculty import Faculty
from ..models.schedule import Schedule, ScheduleEntry

class BacktrackingOptimizer:
    """Backtracking algorithm for schedule optimization and conflict resolution."""
    
    def __init__(self, courses: List[Course], rooms: List[Room], faculty: List[Faculty]):
        self.courses = courses
        self.rooms = rooms
        self.faculty = faculty
        self.faculty_dict = {f.id: f for f in faculty}
        self.room_dict = {r.id: r for r in rooms}
        
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.times = ['08:00', '09:00', '10:00', '11:00', '12:00', 
                     '13:00', '14:00', '15:00', '16:00', '17:00']
        
        # Optimization parameters
        self.max_iterations = 10000
        self.target_accuracy = 99.5
        self.current_iteration = 0
    
    def optimize_schedule(self, initial_schedule: Schedule) -> Schedule:
        """Optimize schedule using backtracking algorithm."""
        self.current_iteration = 0
        
        # Convert schedule to working format
        assignments = self._schedule_to_assignments(initial_schedule)
        unscheduled_courses = self._get_unscheduled_courses(initial_schedule)
        
        # Reset availability based on current schedule
        self._reset_availability()
        self._apply_assignments(assignments)
        
        # Optimize existing assignments and schedule remaining courses
        optimized_assignments = self._backtrack_optimize(assignments, unscheduled_courses, 0)
        
        # Convert back to schedule
        return self._assignments_to_schedule(optimized_assignments)
    
    def _schedule_to_assignments(self, schedule: Schedule) -> List[Dict]:
        """Convert schedule to list of assignments."""
        assignments = []
        for entry in schedule.entries:
            assignment = {
                'course': entry.course,
                'room': entry.room,
                'faculty': entry.faculty,
                'day': entry.day,
                'time': entry.time,
                'duration': entry.duration
            }
            assignments.append(assignment)
        return assignments
    
    def _get_unscheduled_courses(self, schedule: Schedule) -> List[Course]:
        """Get courses that couldn't be scheduled."""
        scheduled_course_ids = {entry.course.id for entry in schedule.entries}
        return [course for course in self.courses if course.id not in scheduled_course_ids]
    
    def _reset_availability(self):
        """Reset room and faculty availability."""
        for room in self.rooms:
            for day in room.availability:
                for time in room.availability[day]:
                    room.availability[day][time] = True
        
        for faculty in self.faculty:
            faculty.assigned_slots = {}
            faculty.current_teaching_hours = 0
    
    def _apply_assignments(self, assignments: List[Dict]):
        """Apply assignments to update availability."""
        for assignment in assignments:
            room = assignment['room']
            faculty = assignment['faculty']
            day = assignment['day']
            time = assignment['time']
            duration = assignment['duration']
            
            room.reserve_slot(day, time, duration)
            faculty.assign_slot(day, time, duration)
    
    def _backtrack_optimize(self, current_assignments: List[Dict], 
                          unscheduled_courses: List[Course], 
                          course_index: int) -> List[Dict]:
        """Main backtracking optimization logic."""
        
        self.current_iteration += 1
        if self.current_iteration > self.max_iterations:
            return current_assignments
        
        # Base case: all courses processed
        if course_index >= len(unscheduled_courses):
            return current_assignments
        
        course = unscheduled_courses[course_index]
        
        # Get all possible assignments for this course
        possible_assignments = self._get_possible_assignments(course)
        
        # Sort by quality score (best first)
        possible_assignments.sort(key=lambda x: self._calculate_assignment_quality(x, course), 
                                reverse=True)
        
        for assignment in possible_assignments:
            # Save current state
            saved_state = self._save_state()
            
            # Try this assignment
            self._apply_assignment(assignment)
            new_assignments = current_assignments + [assignment]
            
            # Check if this leads to a valid solution
            if self._is_valid_state():
                result = self._backtrack_optimize(new_assignments, unscheduled_courses, course_index + 1)
                
                if result is not None:
                    return result
            
            # Backtrack: restore state
            self._restore_state(saved_state)
        
        # No valid assignment found for this course
        return None
    
    def _get_possible_assignments(self, course: Course) -> List[Dict]:
        """Get all possible valid assignments for a course."""
        possible = []
        
        for day in self.days:
            for time in self.times:
                for room in self.rooms:
                    assignment = {
                        'course': course,
                        'room': room,
                        'faculty': self.faculty_dict[course.faculty_id],
                        'day': day,
                        'time': time,
                        'duration': course.duration
                    }
                    
                    if self._is_valid_assignment(assignment, course):
                        possible.append(assignment)
        
        return possible
    
    def _is_valid_assignment(self, assignment: Dict, course: Course) -> bool:
        """Check if assignment satisfies all constraints."""
        room = assignment['room']
        faculty = assignment['faculty']
        day = assignment['day']
        time = assignment['time']
        duration = assignment['duration']
        
        # Hard constraints
        if room.capacity < course.capacity:
            return False
        
        if course.room_type_required and room.room_type.value != course.room_type_required:
            return False
        
        for equipment in course.required_equipment:
            if equipment not in room.equipment:
                return False
        
        if not room.is_available(day, time, duration):
            return False
        
        if not faculty.is_available(day, time, duration):
            return False
        
        return True
    
    def _calculate_assignment_quality(self, assignment: Dict, course: Course) -> float:
        """Calculate comprehensive quality score for assignment."""
        room = assignment['room']
        faculty = assignment['faculty']
        day = assignment['day']
        time = assignment['time']
        
        quality = 1.0
        
        # Preference alignment
        quality *= course.get_constraint_score(day, time, room.id)
        quality *= faculty.get_preference_score(day, time)
        
        # Room utilization efficiency
        utilization = course.capacity / room.capacity
        if 0.8 <= utilization <= 1.0:
            quality *= 1.3
        elif 0.6 <= utilization < 0.8:
            quality *= 1.1
        elif utilization < 0.5:
            quality *= 0.7
        
        # Time distribution bonus (spread courses throughout week)
        quality *= self._calculate_time_distribution_bonus(assignment)
        
        # Consecutive classes bonus for same faculty
        quality *= self._calculate_faculty_continuity_bonus(assignment)
        
        return quality
    
    def _calculate_time_distribution_bonus(self, assignment: Dict) -> float:
        """Bonus for better time distribution."""
        # Simple implementation - can be enhanced
        day = assignment['day']
        time = assignment['time']
        
        # Prefer middle of week and middle of day
        day_bonus = 1.0
        if day in ['Tuesday', 'Wednesday', 'Thursday']:
            day_bonus = 1.1
        
        time_bonus = 1.0
        if time in ['10:00', '11:00', '14:00', '15:00']:
            time_bonus = 1.1
        
        return day_bonus * time_bonus
    
    def _calculate_faculty_continuity_bonus(self, assignment: Dict) -> float:
        """Bonus for faculty schedule continuity."""
        faculty = assignment['faculty']
        day = assignment['day']
        time = assignment['time']
        
        if day not in faculty.assigned_slots:
            return 1.0
        
        times = ['08:00', '09:00', '10:00', '11:00', '12:00', 
                '13:00', '14:00', '15:00', '16:00', '17:00']
        
        if time not in times:
            return 1.0
        
        time_idx = times.index(time)
        assigned_times = faculty.assigned_slots[day]
        
        # Check for adjacent assigned slots
        for assigned_time in assigned_times:
            if assigned_time in times:
                assigned_idx = times.index(assigned_time)
                if abs(assigned_idx - time_idx) == 1:
                    return 1.2  # Bonus for consecutive classes
        
        return 1.0
    
    def _save_state(self) -> Dict:
        """Save current state for backtracking."""
        state = {
            'rooms': deepcopy({r.id: r.availability for r in self.rooms}),
            'faculty': deepcopy({f.id: {
                'assigned_slots': f.assigned_slots,
                'current_teaching_hours': f.current_teaching_hours
            } for f in self.faculty})
        }
        return state
    
    def _restore_state(self, state: Dict):
        """Restore state for backtracking."""
        for room in self.rooms:
            room.availability = deepcopy(state['rooms'][room.id])
        
        for faculty in self.faculty:
            faculty_state = state['faculty'][faculty.id]
            faculty.assigned_slots = deepcopy(faculty_state['assigned_slots'])
            faculty.current_teaching_hours = faculty_state['current_teaching_hours']
    
    def _apply_assignment(self, assignment: Dict):
        """Apply a single assignment."""
        room = assignment['room']
        faculty = assignment['faculty']
        day = assignment['day']
        time = assignment['time']
        duration = assignment['duration']
        
        room.reserve_slot(day, time, duration)
        faculty.assign_slot(day, time, duration)
    
    def _is_valid_state(self) -> bool:
        """Check if current state is valid."""
        # Check for any obvious conflicts
        for faculty in self.faculty:
            if faculty.current_teaching_hours > faculty.max_teaching_hours:
                return False
        
        return True
    
    def _assignments_to_schedule(self, assignments: List[Dict]) -> Schedule:
        """Convert assignments back to schedule."""
        schedule = Schedule()
        
        if assignments:
            for assignment in assignments:
                entry = ScheduleEntry(
                    course=assignment['course'],
                    room=assignment['room'],
                    faculty=assignment['faculty'],
                    day=assignment['day'],
                    time=assignment['time'],
                    duration=assignment['duration']
                )
                
                entry.preference_score = self._calculate_assignment_quality(assignment, assignment['course'])
                entry.resource_efficiency = assignment['course'].capacity / assignment['room'].capacity
                
                schedule.add_entry(entry)
        
        # Add unscheduled courses as conflicts
        scheduled_course_ids = {entry.course.id for entry in schedule.entries}
        for course in self.courses:
            if course.id not in scheduled_course_ids:
                schedule.conflicts.append(f"Could not schedule course {course.code}")
        
        schedule.calculate_metrics()
        return schedule

