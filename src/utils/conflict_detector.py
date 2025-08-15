from typing import List, Dict, Set, Tuple
from ..models.schedule import Schedule, ScheduleEntry
from ..models.course import Course
from ..models.room import Room
from ..models.faculty import Faculty

class ConflictType:
    ROOM_DOUBLE_BOOKING = "room_double_booking"
    FACULTY_DOUBLE_BOOKING = "faculty_double_booking"
    CAPACITY_EXCEEDED = "capacity_exceeded"
    EQUIPMENT_MISSING = "equipment_missing"
    TIME_CONSTRAINT_VIOLATION = "time_constraint_violation"
    FACULTY_OVERLOAD = "faculty_overload"
    ROOM_TYPE_MISMATCH = "room_type_mismatch"
    PREFERENCE_VIOLATION = "preference_violation"

class ConflictDetector:
    """Advanced conflict detection and analysis system."""
    
    def __init__(self):
        self.conflict_weights = {
            ConflictType.ROOM_DOUBLE_BOOKING: 1.0,
            ConflictType.FACULTY_DOUBLE_BOOKING: 1.0,
            ConflictType.CAPACITY_EXCEEDED: 0.9,
            ConflictType.EQUIPMENT_MISSING: 0.8,
            ConflictType.TIME_CONSTRAINT_VIOLATION: 0.7,
            ConflictType.FACULTY_OVERLOAD: 0.6,
            ConflictType.ROOM_TYPE_MISMATCH: 0.5,
            ConflictType.PREFERENCE_VIOLATION: 0.3
        }
    
    def detect_all_conflicts(self, schedule: Schedule) -> Dict[str, List[Dict]]:
        """Detect all types of conflicts in the schedule."""
        conflicts = {
            ConflictType.ROOM_DOUBLE_BOOKING: [],
            ConflictType.FACULTY_DOUBLE_BOOKING: [],
            ConflictType.CAPACITY_EXCEEDED: [],
            ConflictType.EQUIPMENT_MISSING: [],
            ConflictType.TIME_CONSTRAINT_VIOLATION: [],
            ConflictType.FACULTY_OVERLOAD: [],
            ConflictType.ROOM_TYPE_MISMATCH: [],
            ConflictType.PREFERENCE_VIOLATION: []
        }
        
        # Detect room double bookings
        conflicts[ConflictType.ROOM_DOUBLE_BOOKING] = self._detect_room_conflicts(schedule)
        
        # Detect faculty double bookings
        conflicts[ConflictType.FACULTY_DOUBLE_BOOKING] = self._detect_faculty_conflicts(schedule)
        
        # Detect capacity issues
        conflicts[ConflictType.CAPACITY_EXCEEDED] = self._detect_capacity_conflicts(schedule)
        
        # Detect equipment issues
        conflicts[ConflictType.EQUIPMENT_MISSING] = self._detect_equipment_conflicts(schedule)
        
        # Detect time constraint violations
        conflicts[ConflictType.TIME_CONSTRAINT_VIOLATION] = self._detect_time_conflicts(schedule)
        
        # Detect faculty overload
        conflicts[ConflictType.FACULTY_OVERLOAD] = self._detect_faculty_overload(schedule)
        
        # Detect room type mismatches
        conflicts[ConflictType.ROOM_TYPE_MISMATCH] = self._detect_room_type_conflicts(schedule)
        
        # Detect preference violations
        conflicts[ConflictType.PREFERENCE_VIOLATION] = self._detect_preference_violations(schedule)
        
        return conflicts
    
    def _detect_room_conflicts(self, schedule: Schedule) -> List[Dict]:
        """Detect room double booking conflicts."""
        conflicts = []
        room_schedule = {}
        
        for entry in schedule.entries:
            key = (entry.room.id, entry.day, entry.time)
            
            if key not in room_schedule:
                room_schedule[key] = []
            room_schedule[key].append(entry)
        
        for (room_id, day, time), entries in room_schedule.items():
            if len(entries) > 1:
                conflict = {
                    'type': ConflictType.ROOM_DOUBLE_BOOKING,
                    'room_id': room_id,
                    'day': day,
                    'time': time,
                    'conflicting_courses': [entry.course.code for entry in entries],
                    'severity': 'high',
                    'description': f"Room {room_id} double booked on {day} at {time}"
                }
                conflicts.append(conflict)
        
        return conflicts
    
    def _detect_faculty_conflicts(self, schedule: Schedule) -> List[Dict]:
        """Detect faculty double booking conflicts."""
        conflicts = []
        faculty_schedule = {}
        
        for entry in schedule.entries:
            key = (entry.faculty.id, entry.day, entry.time)
            
            if key not in faculty_schedule:
                faculty_schedule[key] = []
            faculty_schedule[key].append(entry)
        
        for (faculty_id, day, time), entries in faculty_schedule.items():
            if len(entries) > 1:
                conflict = {
                    'type': ConflictType.FACULTY_DOUBLE_BOOKING,
                    'faculty_id': faculty_id,
                    'day': day,
                    'time': time,
                    'conflicting_courses': [entry.course.code for entry in entries],
                    'severity': 'high',
                    'description': f"Faculty {faculty_id} double booked on {day} at {time}"
                }
                conflicts.append(conflict)
        
        return conflicts
    
    def _detect_capacity_conflicts(self, schedule: Schedule) -> List[Dict]:
        """Detect room capacity exceeded conflicts."""
        conflicts = []
        
        for entry in schedule.entries:
            if entry.course.capacity > entry.room.capacity:
                conflict = {
                    'type': ConflictType.CAPACITY_EXCEEDED,
                    'course_code': entry.course.code,
                    'room_id': entry.room.id,
                    'required_capacity': entry.course.capacity,
                    'room_capacity': entry.room.capacity,
                    'excess': entry.course.capacity - entry.room.capacity,
                    'severity': 'medium',
                    'description': f"Course {entry.course.code} requires {entry.course.capacity} "
                                 f"seats but room {entry.room.id} only has {entry.room.capacity}"
                }
                conflicts.append(conflict)
        
        return conflicts
    
    def _detect_equipment_conflicts(self, schedule: Schedule) -> List[Dict]:
        """Detect missing equipment conflicts."""
        conflicts = []
        
        for entry in schedule.entries:
            missing_equipment = []
            
            for equipment in entry.course.required_equipment:
                if equipment not in entry.room.equipment:
                    missing_equipment.append(equipment)
            
            if missing_equipment:
                conflict = {
                    'type': ConflictType.EQUIPMENT_MISSING,
                    'course_code': entry.course.code,
                    'room_id': entry.room.id,
                    'missing_equipment': missing_equipment,
                    'severity': 'medium',
                    'description': f"Course {entry.course.code} requires equipment "
                                 f"{missing_equipment} not available in room {entry.room.id}"
                }
                conflicts.append(conflict)
        
        return conflicts
    
    def _detect_time_conflicts(self, schedule: Schedule) -> List[Dict]:
        """Detect time constraint violations."""
        conflicts = []
        
        for entry in schedule.entries:
            violations = []
            
            # Check course time preferences
            if entry.course.preferred_days and entry.day not in entry.course.preferred_days:
                violations.append(f"Day {entry.day} not in preferred days")
            
            if entry.course.preferred_times and entry.time not in entry.course.preferred_times:
                violations.append(f"Time {entry.time} not in preferred times")
            
            # Check faculty unavailable slots
            if (entry.day in entry.faculty.unavailable_slots and 
                entry.time in entry.faculty.unavailable_slots[entry.day]):
                violations.append(f"Faculty unavailable at {entry.day} {entry.time}")
            
            if violations:
                conflict = {
                    'type': ConflictType.TIME_CONSTRAINT_VIOLATION,
                    'course_code': entry.course.code,
                    'faculty_id': entry.faculty.id,
                    'day': entry.day,
                    'time': entry.time,
                    'violations': violations,
                    'severity': 'low',
                    'description': f"Time constraint violations for {entry.course.code}: {violations}"
                }
                conflicts.append(conflict)
        
        return conflicts
    
    def _detect_faculty_overload(self, schedule: Schedule) -> List[Dict]:
        """Detect faculty teaching hour overload."""
        conflicts = []
        faculty_hours = {}
        
        # Calculate total teaching hours per faculty
        for entry in schedule.entries:
            faculty_id = entry.faculty.id
            if faculty_id not in faculty_hours:
                faculty_hours[faculty_id] = 0
            faculty_hours[faculty_id] += entry.duration
        
        # Check against limits
        for entry in schedule.entries:
            faculty = entry.faculty
            total_hours = faculty_hours[faculty.id]
            
            if total_hours > faculty.max_teaching_hours:
                conflict = {
                    'type': ConflictType.FACULTY_OVERLOAD,
                    'faculty_id': faculty.id,
                    'assigned_hours': total_hours,
                    'max_hours': faculty.max_teaching_hours,
                    'overload': total_hours - faculty.max_teaching_hours,
                    'severity': 'medium',
                    'description': f"Faculty {faculty.id} assigned {total_hours} hours "
                                 f"exceeding limit of {faculty.max_teaching_hours}"
                }
                conflicts.append(conflict)
                break  # Only add once per faculty
        
        return conflicts
    
    def _detect_room_type_conflicts(self, schedule: Schedule) -> List[Dict]:
        """Detect room type mismatches."""
        conflicts = []
        
        for entry in schedule.entries:
            if entry.course.room_type_required:
                if entry.room.room_type.value != entry.course.room_type_required:
                    conflict = {
                        'type': ConflictType.ROOM_TYPE_MISMATCH,
                        'course_code': entry.course.code,
                        'room_id': entry.room.id,
                        'required_type': entry.course.room_type_required,
                        'actual_type': entry.room.room_type.value,
                        'severity': 'medium',
                        'description': f"Course {entry.course.code} requires {entry.course.room_type_required} "
                                     f"but assigned to {entry.room.room_type.value}"
                    }
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_preference_violations(self, schedule: Schedule) -> List[Dict]:
        """Detect soft preference violations."""
        conflicts = []
        
        for entry in schedule.entries:
            violations = []
            
            # Faculty preferences
            if entry.faculty.preferred_days and entry.day not in entry.faculty.preferred_days:
                violations.append("Faculty day preference not met")
            
            if entry.faculty.preferred_times and entry.time not in entry.faculty.preferred_times:
                violations.append("Faculty time preference not met")
            
            # Course preferences
            preference_score = entry.course.get_constraint_score(entry.day, entry.time, entry.room.id)
            if preference_score < 0.8:
                violations.append("Course preferences not well satisfied")
            
            if violations:
                conflict = {
                    'type': ConflictType.PREFERENCE_VIOLATION,
                    'course_code': entry.course.code,
                    'faculty_id': entry.faculty.id,
                    'violations': violations,
                    'preference_score': preference_score,
                    'severity': 'low',
                    'description': f"Preference violations for {entry.course.code}: {violations}"
                }
                conflicts.append(conflict)
        
        return conflicts
    
    def calculate_conflict_score(self, conflicts: Dict[str, List[Dict]]) -> float:
        """Calculate overall conflict score (0-100, higher is better)."""
        if not conflicts:
            return 100.0
        
        total_weight = 0
        weighted_conflicts = 0
        
        for conflict_type, conflict_list in conflicts.items():
            if conflict_list:
                weight = self.conflict_weights.get(conflict_type, 0.5)
                total_weight += weight
                weighted_conflicts += len(conflict_list) * weight
        
        if total_weight == 0:
            return 100.0
        
        # Calculate score (higher is better)
        max_possible_conflicts = len(Schedule().entries) if hasattr(Schedule(), 'entries') else 100
        conflict_ratio = min(weighted_conflicts / max_possible_conflicts, 1.0)
        
        return (1.0 - conflict_ratio) * 100
    
    def get_conflict_summary(self, conflicts: Dict[str, List[Dict]]) -> Dict[str, any]:
        """Get summary of all conflicts."""
        summary = {
            'total_conflicts': 0,
            'by_severity': {'high': 0, 'medium': 0, 'low': 0},
            'by_type': {},
            'most_problematic_courses': [],
            'most_problematic_faculty': [],
            'most_problematic_rooms': [],
            'resolution_suggestions': []
        }
        
        course_conflicts = {}
        faculty_conflicts = {}
        room_conflicts = {}
        
        for conflict_type, conflict_list in conflicts.items():
            summary['by_type'][conflict_type] = len(conflict_list)
            summary['total_conflicts'] += len(conflict_list)
            
            for conflict in conflict_list:
                severity = conflict.get('severity', 'medium')
                summary['by_severity'][severity] += 1
                
                # Track problematic entities
                if 'course_code' in conflict:
                    course = conflict['course_code']
                    course_conflicts[course] = course_conflicts.get(course, 0) + 1
                
                if 'faculty_id' in conflict:
                    faculty = conflict['faculty_id']
                    faculty_conflicts[faculty] = faculty_conflicts.get(faculty, 0) + 1
                
                if 'room_id' in conflict:
                    room = conflict['room_id']
                    room_conflicts[room] = room_conflicts.get(room, 0) + 1
        
        # Get most problematic entities
        summary['most_problematic_courses'] = sorted(
            course_conflicts.items(), key=lambda x: x[1], reverse=True
        )[:5]
        
        summary['most_problematic_faculty'] = sorted(
            faculty_conflicts.items(), key=lambda x: x[1], reverse=True
        )[:5]
        
        summary['most_problematic_rooms'] = sorted(
            room_conflicts.items(), key=lambda x: x[1], reverse=True
        )[:5]
        
        # Generate resolution suggestions
        summary['resolution_suggestions'] = self._generate_resolution_suggestions(conflicts)
        
        return summary
    
    def _generate_resolution_suggestions(self, conflicts: Dict[str, List[Dict]]) -> List[str]:
        """Generate suggestions for resolving conflicts."""
        suggestions = []
        
        # Room double booking suggestions
        if conflicts[ConflictType.ROOM_DOUBLE_BOOKING]:
            suggestions.append("Consider adding more rooms or spreading classes across more time slots")
        
        # Faculty double booking suggestions
        if conflicts[ConflictType.FACULTY_DOUBLE_BOOKING]:
            suggestions.append("Review faculty assignments or hire additional faculty")
        
        # Capacity issues
        if conflicts[ConflictType.CAPACITY_EXCEEDED]:
            suggestions.append("Move large courses to bigger rooms or split into multiple sections")
        
        # Equipment issues
        if conflicts[ConflictType.EQUIPMENT_MISSING]:
            suggestions.append("Install required equipment or reassign courses to equipped rooms")
        
        # Faculty overload
        if conflicts[ConflictType.FACULTY_OVERLOAD]:
            suggestions.append("Redistribute teaching load or hire additional faculty")
        
        # Room type mismatches
        if conflicts[ConflictType.ROOM_TYPE_MISMATCH]:
            suggestions.append("Convert rooms to required types or reassign courses")
        
        return suggestions

