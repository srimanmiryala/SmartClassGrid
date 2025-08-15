from typing import List, Dict, Set, Tuple, Optional
from enum import Enum
from ..models.course import Course
from ..models.room import Room
from ..models.faculty import Faculty
from ..models.schedule import Schedule, ScheduleEntry

class ConstraintType(Enum):
    HARD = "hard"
    SOFT = "soft"
    PREFERENCE = "preference"

class Constraint:
    """Represents a scheduling constraint."""
    
    def __init__(self, constraint_type: ConstraintType, weight: float, 
                 description: str, validator_func):
        self.type = constraint_type
        self.weight = weight
        self.description = description
        self.validator = validator_func
    
    def validate(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate assignment against this constraint."""
        return self.validator(assignment, context)

class ConstraintSolver:
    """Advanced constraint satisfaction solver for scheduling."""
    
    def __init__(self, courses: List[Course], rooms: List[Room], faculty: List[Faculty]):
        self.courses = courses
        self.rooms = rooms
        self.faculty = faculty
        
        # Initialize constraint registry
        self.constraints = []
        self._setup_constraints()
        
        # Constraint satisfaction parameters
        self.violation_threshold = 0.1
        self.max_iterations = 5000
        
    def _setup_constraints(self):
        """Setup all scheduling constraints."""
        
        # Hard Constraints (must be satisfied)
        self.constraints.extend([
            Constraint(ConstraintType.HARD, 1.0, "Room capacity sufficient", 
                      self._validate_room_capacity),
            Constraint(ConstraintType.HARD, 1.0, "Room availability", 
                      self._validate_room_availability),
            Constraint(ConstraintType.HARD, 1.0, "Faculty availability", 
                      self._validate_faculty_availability),
            Constraint(ConstraintType.HARD, 1.0, "Required equipment available", 
                      self._validate_equipment),
            Constraint(ConstraintType.HARD, 1.0, "Room type compatibility", 
                      self._validate_room_type),
            Constraint(ConstraintType.HARD, 1.0, "Faculty teaching hours limit", 
                      self._validate_teaching_hours),
        ])
        
        # Soft Constraints (should be satisfied when possible)
        self.constraints.extend([
            Constraint(ConstraintType.SOFT, 0.8, "Faculty preferred days", 
                      self._validate_faculty_day_preference),
            Constraint(ConstraintType.SOFT, 0.7, "Faculty preferred times", 
                      self._validate_faculty_time_preference),
            Constraint(ConstraintType.SOFT, 0.6, "Course time preferences", 
                      self._validate_course_time_preference),
            Constraint(ConstraintType.SOFT, 0.5, "Faculty break requirements", 
                      self._validate_faculty_breaks),
            Constraint(ConstraintType.SOFT, 0.4, "Consecutive hours preference", 
                      self._validate_consecutive_hours),
        ])
        
        # Preference Constraints (optimization targets)
        self.constraints.extend([
            Constraint(ConstraintType.PREFERENCE, 0.3, "Room utilization efficiency", 
                      self._validate_room_utilization),
            Constraint(ConstraintType.PREFERENCE, 0.2, "Building proximity for faculty", 
                      self._validate_building_proximity),
            Constraint(ConstraintType.PREFERENCE, 0.1, "Time distribution balance", 
                      self._validate_time_distribution),
        ])
    
    def solve_constraints(self, initial_schedule: Schedule) -> Schedule:
        """Solve constraints using CSP techniques."""
        
        # Convert schedule to CSP variables
        variables = self._create_csp_variables(initial_schedule)
        
        # Apply constraint propagation
        propagated_variables = self._constraint_propagation(variables)
        
        # Use backtracking with constraint checking
        solution = self._csp_backtrack(propagated_variables, {})
        
        # Convert solution back to schedule
        return self._solution_to_schedule(solution) if solution else initial_schedule
    
    def validate_schedule(self, schedule: Schedule) -> Dict[str, any]:
        """Comprehensive schedule validation."""
        results = {
            'valid': True,
            'hard_violations': [],
            'soft_violations': [],
            'preference_score': 0.0,
            'overall_score': 0.0,
            'constraint_details': {}
        }
        
        total_weight = 0
        total_score = 0
        
        for entry in schedule.entries:
            assignment = {
                'course': entry.course,
                'room': entry.room,
                'faculty': entry.faculty,
                'day': entry.day,
                'time': entry.time,
                'duration': entry.duration
            }
            
            context = {'schedule': schedule, 'entry': entry}
            
            for constraint in self.constraints:
                is_satisfied, score = constraint.validate(assignment, context)
                
                total_weight += constraint.weight
                total_score += score * constraint.weight
                
                if not is_satisfied:
                    if constraint.type == ConstraintType.HARD:
                        results['valid'] = False
                        results['hard_violations'].append(
                            f"{constraint.description}: {entry.course.code}"
                        )
                    elif constraint.type == ConstraintType.SOFT:
                        results['soft_violations'].append(
                            f"{constraint.description}: {entry.course.code}"
                        )
                
                # Track detailed scores
                if constraint.description not in results['constraint_details']:
                    results['constraint_details'][constraint.description] = []
                results['constraint_details'][constraint.description].append(score)
        
        # Calculate overall scores
        results['overall_score'] = (total_score / total_weight) * 100 if total_weight > 0 else 0
        
        # Calculate preference score separately
        preference_score = 0
        preference_weight = 0
        for constraint in self.constraints:
            if constraint.type == ConstraintType.PREFERENCE:
                preference_weight += constraint.weight
                if constraint.description in results['constraint_details']:
                    scores = results['constraint_details'][constraint.description]
                    avg_score = sum(scores) / len(scores) if scores else 0
                    preference_score += avg_score * constraint.weight
        
        results['preference_score'] = (preference_score / preference_weight) * 100 if preference_weight > 0 else 0
        
        return results
    
    # Constraint Validators
    def _validate_room_capacity(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate room capacity constraint."""
        course = assignment['course']
        room = assignment['room']
        
        if room.capacity >= course.capacity:
            # Bonus for optimal utilization
            utilization = course.capacity / room.capacity
            if 0.8 <= utilization <= 1.0:
                return True, 1.0
            elif 0.6 <= utilization < 0.8:
                return True, 0.9
            else:
                return True, 0.7
        
        return False, 0.0
    
    def _validate_room_availability(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate room availability constraint."""
        room = assignment['room']
        day = assignment['day']
        time = assignment['time']
        duration = assignment['duration']
        
        available = room.is_available(day, time, duration)
        return available, 1.0 if available else 0.0
    
    def _validate_faculty_availability(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate faculty availability constraint."""
        faculty = assignment['faculty']
        day = assignment['day']
        time = assignment['time']
        duration = assignment['duration']
        
        available = faculty.is_available(day, time, duration)
        return available, 1.0 if available else 0.0
    
    def _validate_equipment(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate equipment requirements constraint."""
        course = assignment['course']
        room = assignment['room']
        
        for equipment in course.required_equipment:
            if equipment not in room.equipment:
                return False, 0.0
        
        return True, 1.0
    
    def _validate_room_type(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate room type compatibility constraint."""
        course = assignment['course']
        room = assignment['room']
        
        if course.room_type_required:
            if room.room_type.value == course.room_type_required:
                return True, 1.0
            else:
                return False, 0.0
        
        return True, 1.0
    
    def _validate_teaching_hours(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate faculty teaching hours limit constraint."""
        faculty = assignment['faculty']
        duration = assignment['duration']
        
        if faculty.current_teaching_hours + duration <= faculty.max_teaching_hours:
            # Better score for balanced teaching load
            load_ratio = (faculty.current_teaching_hours + duration) / faculty.max_teaching_hours
            if load_ratio <= 0.8:
                return True, 1.0
            else:
                return True, 0.8
        
        return False, 0.0
    
    def _validate_faculty_day_preference(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate faculty day preferences (soft constraint)."""
        faculty = assignment['faculty']
        day = assignment['day']
        
        if not faculty.preferred_days:
            return True, 1.0
        
        if day in faculty.preferred_days:
            return True, 1.0
        else:
            return True, 0.6  # Still valid but lower score
    
    def _validate_faculty_time_preference(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate faculty time preferences (soft constraint)."""
        faculty = assignment['faculty']
        time = assignment['time']
        
        if not faculty.preferred_times:
            return True, 1.0
        
        if time in faculty.preferred_times:
            return True, 1.0
        else:
            return True, 0.6
    
    def _validate_course_time_preference(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate course time preferences (soft constraint)."""
        course = assignment['course']
        day = assignment['day']
        time = assignment['time']
        
        score = course.get_constraint_score(day, time, assignment['room'].id)
        return True, score
    
    def _validate_faculty_breaks(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate faculty break requirements (soft constraint)."""
        faculty = assignment['faculty']
        day = assignment['day']
        time = assignment['time']
        
        if day not in faculty.assigned_slots:
            return True, 1.0
        
        times = ['08:00', '09:00', '10:00', '11:00', '12:00', 
                '13:00', '14:00', '15:00', '16:00', '17:00']
        
        if time not in times:
            return True, 1.0
        
        time_idx = times.index(time)
        assigned_times = faculty.assigned_slots[day]
        
        # Check for adequate breaks
        for assigned_time in assigned_times:
            if assigned_time in times:
                assigned_idx = times.index(assigned_time)
                gap = abs(assigned_idx - time_idx)
                
                if gap == 1:  # Adjacent slots
                    if faculty.consecutive_classes_preference:
                        return True, 1.2  # Bonus for consecutive preference
                    else:
                        return True, 0.7  # Penalty for no break preference
                elif gap < faculty.break_duration_required:
                    return True, 0.5  # Insufficient break
        
        return True, 1.0
    
    def _validate_consecutive_hours(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate consecutive hours requirements (soft constraint)."""
        course = assignment['course']
        
        if not course.consecutive_hours:
            return True, 1.0
        
        duration = assignment['duration']
        if duration > 1:
            return True, 1.0  # Multi-hour courses automatically consecutive
        
        # For single-hour courses that need to be consecutive, 
        # this would require checking against other instances of the same course
        return True, 0.8
    
    def _validate_room_utilization(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate room utilization efficiency (preference constraint)."""
        course = assignment['course']
        room = assignment['room']
        
        utilization = course.capacity / room.capacity
        
        if 0.8 <= utilization <= 1.0:
            return True, 1.0
        elif 0.6 <= utilization < 0.8:
            return True, 0.8
        elif 0.4 <= utilization < 0.6:
            return True, 0.6
        else:
            return True, 0.4
    
    def _validate_building_proximity(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate building proximity for faculty (preference constraint)."""
        # Simple implementation - can be enhanced with actual building data
        return True, 1.0
    
    def _validate_time_distribution(self, assignment: Dict, context: Dict = None) -> Tuple[bool, float]:
        """Validate time distribution balance (preference constraint)."""
        day = assignment['day']
        time = assignment['time']
        
        # Prefer middle days and times
        day_score = 1.0
        if day in ['Tuesday', 'Wednesday', 'Thursday']:
            day_score = 1.1
        elif day in ['Monday', 'Friday']:
            day_score = 0.9
        
        time_score = 1.0
        if time in ['10:00', '11:00', '14:00', '15:00']:
            time_score = 1.1
        elif time in ['08:00', '17:00']:
            time_score = 0.8
        
        return True, day_score * time_score
    
    # CSP Implementation Methods
    def _create_csp_variables(self, schedule: Schedule) -> Dict:
        """Create CSP variables from schedule."""
        variables = {}
        
        for i, entry in enumerate(schedule.entries):
            var_name = f"assignment_{i}"
            variables[var_name] = {
                'course': entry.course,
                'domain': self._get_assignment_domain(entry.course),
                'current_value': {
                    'room': entry.room,
                    'day': entry.day,
                    'time': entry.time
                }
            }
        
        return variables
    
    def _get_assignment_domain(self, course: Course) -> List[Dict]:
        """Get possible assignments (domain) for a course."""
        domain = []
        
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
            for time in ['08:00', '09:00', '10:00', '11:00', '12:00', 
                        '13:00', '14:00', '15:00', '16:00', '17:00']:
                for room in self.rooms:
                    assignment = {
                        'room': room,
                        'day': day,
                        'time': time
                    }
                    
                    # Only include if it satisfies hard constraints
                    full_assignment = {
                        'course': course,
                        'room': room,
                        'faculty': next(f for f in self.faculty if f.id == course.faculty_id),
                        'day': day,
                        'time': time,
                        'duration': course.duration
                    }
                    
                    if self._satisfies_hard_constraints(full_assignment):
                        domain.append(assignment)
        
        return domain
    
    def _satisfies_hard_constraints(self, assignment: Dict) -> bool:
        """Check if assignment satisfies all hard constraints."""
        for constraint in self.constraints:
            if constraint.type == ConstraintType.HARD:
                is_satisfied, _ = constraint.validate(assignment)
                if not is_satisfied:
                    return False
        return True
    
    def _constraint_propagation(self, variables: Dict) -> Dict:
        """Apply constraint propagation to reduce domains."""
        # Arc consistency implementation
        changed = True
        
        while changed:
            changed = False
            
            for var_name, variable in variables.items():
                original_size = len(variable['domain'])
                
                # Filter domain based on constraints
                new_domain = []
                for value in variable['domain']:
                    full_assignment = {
                        'course': variable['course'],
                        'room': value['room'],
                        'faculty': next(f for f in self.faculty if f.id == variable['course'].faculty_id),
                        'day': value['day'],
                        'time': value['time'],
                        'duration': variable['course'].duration
                    }
                    
                    if self._satisfies_hard_constraints(full_assignment):
                        new_domain.append(value)
                
                variable['domain'] = new_domain
                
                if len(variable['domain']) < original_size:
                    changed = True
        
        return variables
    
    def _csp_backtrack(self, variables: Dict, assignment: Dict) -> Optional[Dict]:
        """CSP backtracking search."""
        
        if len(assignment) == len(variables):
            return assignment
        
        # Select unassigned variable (using MRV heuristic)
        unassigned = [var for var in variables if var not in assignment]
        var = min(unassigned, key=lambda v: len(variables[v]['domain']))
        
        # Try each value in domain
        for value in variables[var]['domain']:
            # Check consistency with current assignment
            if self._is_consistent(var, value, assignment, variables):
                assignment[var] = value
                
                result = self._csp_backtrack(variables, assignment)
                if result is not None:
                    return result
                
                del assignment[var]
        
        return None
    
    def _is_consistent(self, var: str, value: Dict, assignment: Dict, variables: Dict) -> bool:
        """Check if assignment is consistent with constraints."""
        # Create full assignment for validation
        course = variables[var]['course']
        full_assignment = {
            'course': course,
            'room': value['room'],
            'faculty': next(f for f in self.faculty if f.id == course.faculty_id),
            'day': value['day'],
            'time': value['time'],
            'duration': course.duration
        }
        
        # Check against already assigned variables
        for assigned_var, assigned_value in assignment.items():
            assigned_course = variables[assigned_var]['course']
            assigned_full = {
                'course': assigned_course,
                'room': assigned_value['room'],
                'faculty': next(f for f in self.faculty if f.id == assigned_course.faculty_id),
                'day': assigned_value['day'],
                'time': assigned_value['time'],
                'duration': assigned_course.duration
            }
            
            # Check for conflicts
            if self._has_conflict(full_assignment, assigned_full):
                return False
        
        return True
    
    def _has_conflict(self, assignment1: Dict, assignment2: Dict) -> bool:
        """Check if two assignments conflict."""
        # Same room, same time
        if (assignment1['room'] == assignment2['room'] and 
            assignment1['day'] == assignment2['day'] and 
            assignment1['time'] == assignment2['time']):
            return True
        
        # Same faculty, same time
        if (assignment1['faculty'] == assignment2['faculty'] and 
            assignment1['day'] == assignment2['day'] and 
            assignment1['time'] == assignment2['time']):
            return True
        
        return False
    
    def _solution_to_schedule(self, solution: Dict) -> Schedule:
        """Convert CSP solution back to schedule."""
        schedule = Schedule()
        
        for var_name, value in solution.items():
            var_parts = var_name.split('_')
            if len(var_parts) == 2 and var_parts[0] == 'assignment':
                index = int(var_parts[1])
                
                # Find corresponding course
                course = None
                for c in self.courses:
                    if c.id == value.get('course_id'):
                        course = c
                        break
                
                if course:
                    faculty = next(f for f in self.faculty if f.id == course.faculty_id)
                    
                    entry = ScheduleEntry(
                        course=course,
                        room=value['room'],
                        faculty=faculty,
                        day=value['day'],
                        time=value['time'],
                        duration=course.duration
                    )
                    
                    schedule.add_entry(entry)
        
        schedule.calculate_metrics()
        return schedule

