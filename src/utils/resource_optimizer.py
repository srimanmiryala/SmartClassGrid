from typing import List, Dict, Tuple, Optional
import numpy as np
from ..models.schedule import Schedule, ScheduleEntry
from ..models.room import Room
from ..models.faculty import Faculty

class ResourceOptimizer:
    """Advanced resource optimization for maximum efficiency."""
    
    def __init__(self, rooms: List[Room], faculty: List[Faculty]):
        self.rooms = rooms
        self.faculty = faculty
        self.room_dict = {r.id: r for r in rooms}
        self.faculty_dict = {f.id: f for f in faculty}
        
        # Optimization parameters
        self.target_room_utilization = 0.85
        self.target_faculty_load = 0.8
        self.optimization_weights = {
            'room_utilization': 0.4,
            'faculty_balance': 0.3,
            'preference_satisfaction': 0.2,
            'resource_efficiency': 0.1
        }
    
    def optimize_resource_allocation(self, schedule: Schedule) -> Tuple[Schedule, Dict[str, float]]:
        """Optimize resource allocation for maximum efficiency."""
        
        # Calculate current metrics
        initial_metrics = self.calculate_resource_metrics(schedule)
        
        # Apply optimization strategies
        optimized_schedule = schedule
        
        # 1. Room utilization optimization
        optimized_schedule = self._optimize_room_utilization(optimized_schedule)
        
        # 2. Faculty load balancing
        optimized_schedule = self._optimize_faculty_load_balancing(optimized_schedule)
        
        # 3. Time slot optimization
        optimized_schedule = self._optimize_time_distribution(optimized_schedule)
        
        # 4. Resource efficiency optimization
        optimized_schedule = self._optimize_resource_efficiency(optimized_schedule)
        
        # Calculate final metrics
        final_metrics = self.calculate_resource_metrics(optimized_schedule)
        
        # Calculate improvement
        improvement_metrics = {
            'room_utilization_improvement': final_metrics['average_room_utilization'] - initial_metrics['average_room_utilization'],
            'faculty_balance_improvement': final_metrics['faculty_load_balance'] - initial_metrics['faculty_load_balance'],
            'efficiency_improvement': final_metrics['overall_efficiency'] - initial_metrics['overall_efficiency']
        }
        
        return optimized_schedule, improvement_metrics
    
    def calculate_resource_metrics(self, schedule: Schedule) -> Dict[str, float]:
        """Calculate comprehensive resource utilization metrics."""
        metrics = {
            'room_utilization_by_room': {},
            'faculty_load_by_faculty': {},
            'average_room_utilization': 0.0,
            'room_utilization_variance': 0.0,
            'faculty_load_balance': 0.0,
            'time_distribution_balance': 0.0,
            'resource_efficiency_score': 0.0,
            'overall_efficiency': 0.0
        }
        
        # Calculate room utilization
        room_usage = {room.id: 0 for room in self.rooms}
        total_room_hours = len(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']) * \
                          len(['08:00', '09:00', '10:00', '11:00', '12:00', 
                              '13:00', '14:00', '15:00', '16:00', '17:00'])
        
        for entry in schedule.entries:
            room_usage[entry.room.id] += entry.duration
        
        # Room utilization by room
        for room_id, usage in room_usage.items():
            utilization = (usage / total_room_hours) * 100
            metrics['room_utilization_by_room'][room_id] = utilization
        
        # Average room utilization
        utilizations = list(metrics['room_utilization_by_room'].values())
        metrics['average_room_utilization'] = np.mean(utilizations) if utilizations else 0
        metrics['room_utilization_variance'] = np.var(utilizations) if utilizations else 0
        
        # Faculty load analysis
        faculty_usage = {faculty.id: 0 for faculty in self.faculty}
        
        for entry in schedule.entries:
            faculty_usage[entry.faculty.id] += entry.duration
        
        for faculty_id, usage in faculty_usage.items():
            faculty = self.faculty_dict[faculty_id]
            load_percentage = (usage / faculty.max_teaching_hours) * 100
            metrics['faculty_load_by_faculty'][faculty_id] = load_percentage
        
        # Faculty load balance (lower variance is better)
        faculty_loads = list(metrics['faculty_load_by_faculty'].values())
        if faculty_loads:
            load_variance = np.var(faculty_loads)
            metrics['faculty_load_balance'] = max(0, 100 - load_variance)  # Convert to score
        
        # Time distribution balance
        time_usage = {}
        for entry in schedule.entries:
            time_key = f"{entry.day}_{entry.time}"
            time_usage[time_key] = time_usage.get(time_key, 0) + 1
        
        if time_usage:
            time_variance = np.var(list(time_usage.values()))
            metrics['time_distribution_balance'] = max(0, 100 - time_variance * 2)
        
        # Resource efficiency score
        efficiency_scores = []
        for entry in schedule.entries:
            room_efficiency = entry.course.capacity / entry.room.capacity
            efficiency_scores.append(min(room_efficiency, 1.0))
        
        metrics['resource_efficiency_score'] = np.mean(efficiency_scores) * 100 if efficiency_scores else 0
        
        # Overall efficiency (weighted combination)
        weights = self.optimization_weights
        metrics['overall_efficiency'] = (
            metrics['average_room_utilization'] * weights['room_utilization'] +
            metrics['faculty_load_balance'] * weights['faculty_balance'] +
            metrics['resource_efficiency_score'] * weights['resource_efficiency'] +
            metrics['time_distribution_balance'] * weights['preference_satisfaction']
        )
        
        return metrics
    
    def _optimize_room_utilization(self, schedule: Schedule) -> Schedule:
        """Optimize room utilization by reassigning courses to better-sized rooms."""
        optimized_entries = []
        
        for entry in schedule.entries:
            # Find better room if current one is inefficient
            current_efficiency = entry.course.capacity / entry.room.capacity
            
            if current_efficiency < 0.6:  # Room too large
                better_room = self._find_better_room(entry, prefer_smaller=True)
                if better_room:
                    # Check if room is available
                    if better_room.is_available(entry.day, entry.time, entry.duration):
                        # Update room assignment
                        new_entry = ScheduleEntry(
                            course=entry.course,
                            room=better_room,
                            faculty=entry.faculty,
                            day=entry.day,
                            time=entry.time,
                            duration=entry.duration
                        )
                        
                        # Reserve new room and free old room
                        better_room.reserve_slot(entry.day, entry.time, entry.duration)
                        self._free_room_slot(entry.room, entry.day, entry.time, entry.duration)
                        
                        optimized_entries.append(new_entry)
                        continue
            
            optimized_entries.append(entry)
        
        # Create new schedule
        optimized_schedule = Schedule()
        optimized_schedule.entries = optimized_entries
        optimized_schedule.calculate_metrics()
        
        return optimized_schedule
    
    def _find_better_room(self, entry: ScheduleEntry, prefer_smaller: bool = True) -> Optional[Room]:
        """Find a better room for the given entry."""
        course = entry.course
        current_room = entry.room
        
        # Get candidate rooms
        candidates = []
        for room in self.rooms:
            if room.id == current_room.id:
                continue
            
            # Check basic compatibility
            if room.capacity < course.capacity:
                continue
            
            if course.room_type_required and room.room_type.value != course.room_type_required:
                continue
            
            # Check equipment
            if not all(eq in room.equipment for eq in course.required_equipment):
                continue
            
            candidates.append(room)
        
        if not candidates:
            return None
        
        # Sort by efficiency
        if prefer_smaller:
            # Prefer rooms closer to course capacity
            candidates.sort(key=lambda r: r.capacity)
        else:
            # Prefer larger rooms
            candidates.sort(key=lambda r: r.capacity, reverse=True)
        
        # Return best candidate that provides better efficiency
        for room in candidates:
            new_efficiency = course.capacity / room.capacity
            current_efficiency = course.capacity / current_room.capacity
            
            if prefer_smaller and new_efficiency > current_efficiency:
                return room
            elif not prefer_smaller and room.capacity > current_room.capacity:
                return room
        
        return None
    
    def _free_room_slot(self, room: Room, day: str, time: str, duration: int):
        """Free up room slot."""
        times = ['08:00', '09:00', '10:00', '11:00', '12:00', 
                '13:00', '14:00', '15:00', '16:00', '17:00']
        
        if time in times:
            start_idx = times.index(time)
            for i in range(duration):
                if start_idx + i < len(times):
                    free_time = times[start_idx + i]
                    if day in room.availability and free_time in room.availability[day]:
                        room.availability[day][free_time] = True
    
    def _optimize_faculty_load_balancing(self, schedule: Schedule) -> Schedule:
        """Balance faculty teaching loads."""
        # Calculate current loads
        faculty_loads = {}
        faculty_courses = {}
        
        for entry in schedule.entries:
            faculty_id = entry.faculty.id
            faculty_loads[faculty_id] = faculty_loads.get(faculty_id, 0) + entry.duration
            
            if faculty_id not in faculty_courses:
                faculty_courses[faculty_id] = []
            faculty_courses[faculty_id].append(entry)
        
        # Identify overloaded and underloaded faculty
        overloaded = []
        underloaded = []
        
        for faculty in self.faculty:
            load = faculty_loads.get(faculty.id, 0)
            load_ratio = load / faculty.max_teaching_hours
            
            if load_ratio > 0.9:  # 90% or more
                overloaded.append((faculty, load))
            elif load_ratio < 0.6:  # Less than 60%
                underloaded.append((faculty, load))
        
        # Try to redistribute courses
        optimized_entries = list(schedule.entries)
        
        for overloaded_faculty, _ in overloaded:
            courses_to_reassign = faculty_courses.get(overloaded_faculty.id, [])
            
            # Sort by flexibility (courses with fewer constraints first)
            courses_to_reassign.sort(key=lambda e: len(e.course.required_equipment))
            
            for entry in courses_to_reassign:
                for underloaded_faculty, _ in underloaded:
                    # Check if underloaded faculty can teach this course
                    if self._can_faculty_teach_course(underloaded_faculty, entry.course):
                        # Check availability
                        if underloaded_faculty.is_available(entry.day, entry.time, entry.duration):
                            # Reassign course
                            new_entry = ScheduleEntry(
                                course=entry.course,
                                room=entry.room,
                                faculty=underloaded_faculty,
                                day=entry.day,
                                time=entry.time,
                                duration=entry.duration
                            )
                            
                            # Update entries
                            optimized_entries.remove(entry)
                            optimized_entries.append(new_entry)
                            
                            # Update loads
                            faculty_loads[overloaded_faculty.id] -= entry.duration
                            faculty_loads[underloaded_faculty.id] = faculty_loads.get(underloaded_faculty.id, 0) + entry.duration
                            
                            break
        
        # Create optimized schedule
        optimized_schedule = Schedule()
        optimized_schedule.entries = optimized_entries
        optimized_schedule.calculate_metrics()
        
        return optimized_schedule
    
    def _can_faculty_teach_course(self, faculty: Faculty, course) -> bool:
        """Check if faculty can teach the given course."""
        # Check department compatibility
        if faculty.department != course.department:
            return False
        
        # Check if faculty has capacity
        if faculty.current_teaching_hours + course.duration > faculty.max_teaching_hours:
            return False
        
        return True
    
    def _optimize_time_distribution(self, schedule: Schedule) -> Schedule:
        """Optimize time distribution to spread courses evenly."""
        # Analyze current time distribution
        time_slots = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        times = ['08:00', '09:00', '10:00', '11:00', '12:00', 
                '13:00', '14:00', '15:00', '16:00', '17:00']
        
        for day in days:
            for time in times:
                time_slots[f"{day}_{time}"] = 0
        
        for entry in schedule.entries:
            time_key = f"{entry.day}_{entry.time}"
            time_slots[time_key] += 1
        
        # Find overcrowded and undercrowded slots
        avg_usage = np.mean(list(time_slots.values()))
        overcrowded = [(slot, count) for slot, count in time_slots.items() if count > avg_usage * 1.5]
        undercrowded = [(slot, count) for slot, count in time_slots.items() if count < avg_usage * 0.5]
        
        # Try to move courses from overcrowded to undercrowded slots
        optimized_entries = list(schedule.entries)
        
        for overcrowded_slot, _ in overcrowded:
            day, time = overcrowded_slot.split('_')
            
            # Find courses in this slot
            slot_entries = [e for e in optimized_entries if e.day == day and e.time == time]
            
            # Sort by flexibility (fewer constraints = more flexible)
            slot_entries.sort(key=lambda e: len(e.course.preferred_times) + len(e.course.preferred_days))
            
            for entry in slot_entries:
                # Try to move to undercrowded slot
                for undercrowded_slot, _ in undercrowded:
                    new_day, new_time = undercrowded_slot.split('_')
                    
                    # Check if move is possible
                    if self._can_move_entry(entry, new_day, new_time):
                        # Create new entry
                        new_entry = ScheduleEntry(
                            course=entry.course,
                            room=entry.room,
                            faculty=entry.faculty,
                            day=new_day,
                            time=new_time,
                            duration=entry.duration
                        )
                        
                        # Update entries
                        optimized_entries.remove(entry)
                        optimized_entries.append(new_entry)
                        
                        # Update slot counts
                        time_slots[overcrowded_slot] -= 1
                        time_slots[undercrowded_slot] += 1
                        
                        break
        
        # Create optimized schedule
        optimized_schedule = Schedule()
        optimized_schedule.entries = optimized_entries
        optimized_schedule.calculate_metrics()
        
        return optimized_schedule
    
    def _can_move_entry(self, entry: ScheduleEntry, new_day: str, new_time: str) -> bool:
        """Check if entry can be moved to new time slot."""
        # Check room availability
        if not entry.room.is_available(new_day, new_time, entry.duration):
            return False
        
        # Check faculty availability
        if not entry.faculty.is_available(new_day, new_time, entry.duration):
            return False
        
        # Check course preferences (soft constraint)
        if entry.course.preferred_days and new_day not in entry.course.preferred_days:
            return False
        
        if entry.course.preferred_times and new_time not in entry.course.preferred_times:
            return False
        
        return True
    
    def _optimize_resource_efficiency(self, schedule: Schedule) -> Schedule:
        """Optimize overall resource efficiency."""
        optimized_entries = list(schedule.entries)
        
        # Sort entries by current efficiency (least efficient first)
        efficiency_entries = []
        for entry in optimized_entries:
            efficiency = entry.course.capacity / entry.room.capacity
            efficiency_entries.append((entry, efficiency))
        
        efficiency_entries.sort(key=lambda x: x[1])  # Lowest efficiency first
        
        # Try to improve efficiency for worst cases
        for entry, current_efficiency in efficiency_entries[:10]:  # Top 10 worst
            if current_efficiency < 0.7:  # Only if efficiency is poor
                # Try to find better assignment
                better_assignment = self._find_better_assignment(entry)
                
                if better_assignment:
                    # Update entry
                    optimized_entries.remove(entry)
                    optimized_entries.append(better_assignment)
        
        # Create optimized schedule
        optimized_schedule = Schedule()
        optimized_schedule.entries = optimized_entries
        optimized_schedule.calculate_metrics()
        
        return optimized_schedule
    
    def _find_better_assignment(self, entry: ScheduleEntry) -> Optional[ScheduleEntry]:
        """Find a better overall assignment for the entry."""
        current_score = self._calculate_entry_score(entry)
        best_assignment = None
        best_score = current_score
        
        # Try different rooms
        for room in self.rooms:
            if room.id == entry.room.id:
                continue
            
            # Check basic compatibility
            if not self._is_room_compatible(entry.course, room):
                continue
            
            # Check availability
            if not room.is_available(entry.day, entry.time, entry.duration):
                continue
            
            # Create test assignment
            test_entry = ScheduleEntry(
                course=entry.course,
                room=room,
                faculty=entry.faculty,
                day=entry.day,
                time=entry.time,
                duration=entry.duration
            )
            
            score = self._calculate_entry_score(test_entry)
            if score > best_score:
                best_score = score
                best_assignment = test_entry
        
        return best_assignment
    
    def _is_room_compatible(self, course, room: Room) -> bool:
        """Check if room is compatible with course requirements."""
        if room.capacity < course.capacity:
            return False
        
        if course.room_type_required and room.room_type.value != course.room_type_required:
            return False
        
        for equipment in course.required_equipment:
            if equipment not in room.equipment:
                return False
        
        return True
    
    def _calculate_entry_score(self, entry: ScheduleEntry) -> float:
        """Calculate overall score for a schedule entry."""
        score = 1.0
        
        # Room efficiency
        room_efficiency = entry.course.capacity / entry.room.capacity
        if 0.8 <= room_efficiency <= 1.0:
            score *= 1.3
        elif 0.6 <= room_efficiency < 0.8:
            score *= 1.1
        elif room_efficiency < 0.5:
            score *= 0.6
        
        # Preference alignment
        course_score = entry.course.get_constraint_score(entry.day, entry.time, entry.room.id)
        faculty_score = entry.faculty.get_preference_score(entry.day, entry.time)
        
        score *= (course_score + faculty_score) / 2
        
        # Room quality
        room_quality = (entry.room.acoustics_rating + entry.room.lighting_rating) / 2
        score *= room_quality
        
        return score
    
    def generate_optimization_report(self, initial_metrics: Dict[str, float], 
                                   final_metrics: Dict[str, float]) -> Dict[str, any]:
        """Generate comprehensive optimization report."""
        report = {
            'optimization_summary': {
                'room_utilization_improvement': final_metrics['average_room_utilization'] - initial_metrics['average_room_utilization'],
                'faculty_balance_improvement': final_metrics['faculty_load_balance'] - initial_metrics['faculty_load_balance'],
                'efficiency_improvement': final_metrics['overall_efficiency'] - initial_metrics['overall_efficiency'],
                'resource_efficiency_improvement': final_metrics['resource_efficiency_score'] - initial_metrics['resource_efficiency_score']
            },
            'detailed_metrics': {
                'before': initial_metrics,
                'after': final_metrics
            },
            'recommendations': [],
            'optimization_score': 0.0
        }
        
        # Calculate optimization score
        improvements = report['optimization_summary']
        positive_improvements = sum(1 for improvement in improvements.values() if improvement > 0)
        report['optimization_score'] = (positive_improvements / len(improvements)) * 100
        
        # Generate recommendations
        if final_metrics['average_room_utilization'] < 70:
            report['recommendations'].append("Consider reducing number of rooms or increasing course offerings")
        
        if final_metrics['faculty_load_balance'] < 80:
            report['recommendations'].append("Review faculty assignments for better load distribution")
        
        if final_metrics['resource_efficiency_score'] < 80:
            report['recommendations'].append("Optimize room assignments to match course capacities better")
        
        return report

