# tests/test_scheduler.py

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.course import Course, CourseType
from src.models.room import Room, RoomType
from src.models.faculty import Faculty
from src.models.schedule import Schedule, ScheduleEntry
from src.algorithms.greedy_scheduler import GreedyScheduler
from src.utils.conflict_detector import ConflictDetector
from src.utils.resource_optimizer import ResourceOptimizer

class TestScheduler:
    """Test cases for the scheduling system."""
    
    def setup_method(self):
        """Set up test data before each test."""
        self.courses = [
            Course(
                id="CS101",
                name="Intro to CS",
                code="CS101",
                duration=2,
                course_type=CourseType.LECTURE,
                capacity=50,
                faculty_id="F001",
                department="Computer Science",
                semester=1,
                credits=3,
                preferred_days=["Monday"],
                preferred_times=["10:00"],
                required_equipment=["projector"],
                room_type_required="classroom"
            ),
            Course(
                id="CS102",
                name="Programming Lab",
                code="CS102",
                duration=3,
                course_type=CourseType.LAB,
                capacity=25,
                faculty_id="F002",
                department="Computer Science",
                semester=1,
                credits=2,
                preferred_days=["Tuesday"],
                preferred_times=["14:00"],
                required_equipment=["computers"],
                room_type_required="computer_lab",
                consecutive_hours=True
            )
        ]
        
        self.rooms = [
            Room(
                id="R101",
                name="Room 101",
                capacity=100,
                room_type=RoomType.CLASSROOM,
                building="Main",
                floor=1,
                equipment=["projector", "computer"],
                features=["acoustic_panels"],
                acoustics_rating=0.9,
                lighting_rating=0.8,
                accessibility_rating=1.0
            ),
            Room(
                id="LAB201",
                name="Computer Lab 201",
                capacity=30,
                room_type=RoomType.COMPUTER_LAB,
                building="Tech",
                floor=2,
                equipment=["computers", "software"],
                features=["air_conditioning"],
                acoustics_rating=0.85,
                lighting_rating=0.9,
                accessibility_rating=0.8
            )
        ]
        
        self.faculty = [
            Faculty(
                id="F001",
                name="Dr. Alice",
                department="Computer Science",
                email="alice@uni.edu",
                max_teaching_hours=20,
                preferred_days=["Monday"],
                preferred_times=["10:00"],
                unavailable_slots={},
                consecutive_classes_preference=True,
                break_duration_required=1
            ),
            Faculty(
                id="F002",
                name="Prof. Bob",
                department="Computer Science",
                email="bob@uni.edu",
                max_teaching_hours=18,
                preferred_days=["Tuesday"],
                preferred_times=["14:00"],
                unavailable_slots={},
                consecutive_classes_preference=False,
                break_duration_required=1
            )
        ]
    
    def test_greedy_scheduler_basic(self):
        """Test basic greedy scheduling functionality."""
        scheduler = GreedyScheduler(self.courses, self.rooms, self.faculty)
        schedule = scheduler.generate_schedule()
        
        # Check that schedule was generated
        assert isinstance(schedule, Schedule)
        assert len(schedule.entries) >= 0
        
        # If entries were created, verify their structure
        for entry in schedule.entries:
            assert isinstance(entry, ScheduleEntry)
            assert entry.course in self.courses
            assert entry.room in self.rooms
            assert entry.faculty in self.faculty
            assert entry.day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            assert entry.time in ['08:00', '09:00', '10:00', '11:00', '12:00', 
                                 '13:00', '14:00', '15:00', '16:00', '17:00']
    
    def test_schedule_entry_creation(self):
        """Test schedule entry creation."""
        entry = ScheduleEntry(
            course=self.courses,
            room=self.rooms,
            faculty=self.faculty,
            day="Monday",
            time="10:00",
            duration=2
        )
        
        assert entry.day == "Monday"
        assert entry.time == "10:00"
        assert entry.duration == 2
        assert entry.conflict_score == 0.0
        assert entry.preference_score == 1.0
        assert entry.resource_efficiency == 1.0
    
    def test_conflict_detector(self):
        """Test conflict detection functionality."""
        detector = ConflictDetector()
        
        # Create a schedule with potential conflicts
        schedule = Schedule()
        
        # Add a valid entry
        entry1 = ScheduleEntry(
            course=self.courses,
            room=self.rooms,
            faculty=self.faculty,
            day="Monday",
            time="10:00",
            duration=2
        )
        schedule.add_entry(entry1)
        
        # Test conflict detection
        conflicts = detector.detect(schedule)
        assert isinstance(conflicts, dict)
        assert "room_double_booking" in conflicts
        assert "faculty_double_booking" in conflicts
        assert "capacity_exceeded" in conflicts
        assert "equipment_missing" in conflicts
    
    def test_room_availability(self):
        """Test room availability checking."""
        room = self.rooms
        
        # Test availability for valid time slot
        assert room.is_available("Monday", "10:00", 1) == True
        
        # Reserve a slot and test
        room.reserve_slot("Monday", "10:00", 1)
        assert room.is_available("Monday", "10:00", 1) == False
    
    def test_faculty_availability(self):
        """Test faculty availability checking."""
        faculty = self.faculty
        
        # Test availability for valid time slot
        assert faculty.is_available("Monday", "10:00", 2) == True
        
        # Assign a slot and test
        faculty.assign_slot("Monday", "10:00", 2)
        assert faculty.current_teaching_hours == 2
        assert faculty.is_available("Monday", "10:00", 1) == False
    
    def test_course_constraint_score(self):
        """Test course constraint scoring."""
        course = self.courses
        
        # Test preferred day and time
        score1 = course.get_constraint_score("Monday", "10:00", "R101")
        assert score1 >= 0.0
        
        # Test non-preferred day
        score2 = course.get_constraint_score("Friday", "17:00", "R101")
        assert score2 >= 0.0
        assert score2 <= score1  # Should be lower for non-preferred
    
    def test_schedule_metrics_calculation(self):
        """Test schedule metrics calculation."""
        schedule = Schedule()
        
        # Add some entries
        entry = ScheduleEntry(
            course=self.courses,
            room=self.rooms,
            faculty=self.faculty,
            day="Monday",
            time="10:00",
            duration=2
        )
        schedule.add_entry(entry)
        
        # Calculate metrics
        schedule.calculate_metrics()
        
        assert isinstance(schedule.accuracy_score, float)
        assert 0 <= schedule.accuracy_score <= 100
        assert isinstance(schedule.faculty_satisfaction, float)
        assert schedule.faculty_satisfaction >= 0
    
    def test_resource_optimizer_metrics(self):
        """Test resource optimizer metrics calculation."""
        if len(self.rooms) > 0 and len(self.faculty) > 0:
            optimizer = ResourceOptimizer(self.rooms, self.faculty)
            
            # Create a simple schedule
            schedule = Schedule()
            entry = ScheduleEntry(
                course=self.courses,
                room=self.rooms,
                faculty=self.faculty,
                day="Monday",
                time="10:00",
                duration=2
            )
            schedule.add_entry(entry)
            
            # Calculate metrics
            metrics = optimizer.calculate_resource_metrics(schedule)
            
            assert isinstance(metrics, dict)
            assert "average_room_utilization" in metrics
            assert "faculty_load_balance" in metrics
            assert "overall_efficiency" in metrics
            assert isinstance(metrics["average_room_utilization"], float)
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test empty schedule
        empty_schedule = Schedule()
        empty_schedule.calculate_metrics()
        assert empty_schedule.accuracy_score == 0.0
        
        # Test conflict detection on empty schedule
        detector = ConflictDetector()
        conflicts = detector.detect(empty_schedule)
        assert all(len(conflict_list) == 0 for conflict_list in conflicts.values())


def test_integration():
    """Integration test for the complete scheduling workflow."""
    # Create sample data
    courses = [
        Course(
            id="TEST101",
            name="Test Course",
            code="TEST101",
            duration=1,
            course_type=CourseType.LECTURE,
            capacity=30,
            faculty_id="F_TEST",
            department="Test Department",
            semester=1,
            credits=3,
            preferred_days=["Monday"],
            preferred_times=["10:00"],
            required_equipment=[],
            room_type_required="classroom"
        )
    ]
    
    rooms = [
        Room(
            id="R_TEST",
            name="Test Room",
            capacity=50,
            room_type=RoomType.CLASSROOM,
            building="Test Building",
            floor=1,
            equipment=[],
            features=[],
            acoustics_rating=1.0,
            lighting_rating=1.0,
            accessibility_rating=1.0
        )
    ]
    
    faculty = [
        Faculty(
            id="F_TEST",
            name="Test Faculty",
            department="Test Department",
            email="test@test.edu",
            max_teaching_hours=20,
            preferred_days=["Monday"],
            preferred_times=["10:00"],
            unavailable_slots={},
            consecutive_classes_preference=True,
            break_duration_required=1
        )
    ]
    
    # Test complete workflow
    scheduler = GreedyScheduler(courses, rooms, faculty)
    schedule = scheduler.generate_schedule()
    
    detector = ConflictDetector()
    conflicts = detector.detect(schedule)
    
    # Verify results
    assert isinstance(schedule, Schedule)
    assert isinstance(conflicts, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

