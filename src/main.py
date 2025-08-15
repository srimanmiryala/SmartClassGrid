# src/main.py

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import traceback

# Add project root to Python path to fix imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import models
from src.models.course import Course, CourseType
from src.models.room import Room, RoomType
from src.models.faculty import Faculty
from src.models.schedule import Schedule

# Import algorithms
from src.algorithms.greedy_scheduler import GreedyScheduler
from src.algorithms.backtracking_optimizer import BacktrackingOptimizer
from src.algorithms.constraint_solver import ConstraintSolver

# Import utilities
from src.utils.conflict_detector import ConflictDetector
from src.utils.resource_optimizer import ResourceOptimizer

# Import UI
from src.ui.main_window import SchedulingApp

class SmartClassGrid:
    """Main application class for the SmartClassGrid scheduling system."""
    
    def __init__(self):
        self.courses: List[Course] = []
        self.rooms: List[Room] = []
        self.faculty: List[Faculty] = []
        self.current_schedule: Optional[Schedule] = None
        
        # Initialize components
        self.conflict_detector = ConflictDetector()
        self.resource_optimizer = None  # Will be initialized after loading data
        self.constraint_solver = None   # Will be initialized after loading data
        
        # Performance tracking
        self.metrics = {
            'accuracy': 0.0,
            'conflicts_eliminated': 0.0,
            'room_utilization_improvement': 0.0,
            'constraint_satisfaction': 0.0
        }
        
        # Optimization metrics
        self.last_optimization_metrics = {}
    
    def load_data(self):
        """Load course, room, and faculty data from JSON files."""
        try:
            # Try to load from JSON files first
            data_dir = Path(__file__).parent.parent / "data"
            
            if self._load_from_json_files(data_dir):
                print(f"✓ Loaded data from JSON files:")
                print(f"  Courses: {len(self.courses)}")
                print(f"  Rooms: {len(self.rooms)}")
                print(f"  Faculty: {len(self.faculty)}")
            else:
                # Fallback to sample data
                print("⚠ JSON files not found, using sample data...")
                self._create_sample_data()
            
            # FIX 1: Initialize resource optimizer after loading data
            if self.rooms and self.faculty:
                self.resource_optimizer = ResourceOptimizer(self.rooms, self.faculty)
                print("✓ Resource optimizer initialized")
            
            # Initialize constraint solver
            if self.courses and self.rooms and self.faculty:
                self.constraint_solver = ConstraintSolver(self.courses, self.rooms, self.faculty)
                print("✓ Constraint solver initialized")
                
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            print("Using sample data as fallback...")
            self._create_sample_data()
            
            # Initialize optimizers with sample data
            if self.rooms and self.faculty:
                self.resource_optimizer = ResourceOptimizer(self.rooms, self.faculty)
                print("✓ Resource optimizer initialized with sample data")
            
            if self.courses and self.rooms and self.faculty:
                self.constraint_solver = ConstraintSolver(self.courses, self.rooms, self.faculty)
                print("✓ Constraint solver initialized with sample data")
    
    def _load_from_json_files(self, data_dir: Path) -> bool:
        """Load data from JSON files."""
        try:
            # Load courses
            courses_file = data_dir / "courses.json"
            if courses_file.exists():
                with open(courses_file, 'r', encoding='utf-8') as f:
                    courses_data = json.load(f)
                    self.courses = [self._dict_to_course(course_dict) for course_dict in courses_data]
            
            # Load rooms
            rooms_file = data_dir / "rooms.json"
            if rooms_file.exists():
                with open(rooms_file, 'r', encoding='utf-8') as f:
                    rooms_data = json.load(f)
                    self.rooms = [self._dict_to_room(room_dict) for room_dict in rooms_data]
            
            # Load faculty
            faculty_file = data_dir / "faculty.json"
            if faculty_file.exists():
                with open(faculty_file, 'r', encoding='utf-8') as f:
                    faculty_data = json.load(f)
                    self.faculty = [self._dict_to_faculty(faculty_dict) for faculty_dict in faculty_data]
            
            return len(self.courses) > 0 and len(self.rooms) > 0 and len(self.faculty) > 0
            
        except Exception as e:
            print(f"Error loading JSON files: {e}")
            return False
    
    def _dict_to_course(self, course_dict: Dict) -> Course:
        """Convert dictionary to Course object."""
        return Course(
            id=course_dict.get("id", ""),
            name=course_dict.get("name", ""),
            code=course_dict.get("code", ""),
            duration=course_dict.get("duration", 1),
            course_type=CourseType(course_dict.get("course_type", "LECTURE")),
            capacity=course_dict.get("capacity", 0),
            faculty_id=course_dict.get("faculty_id", ""),
            department=course_dict.get("department", ""),
            semester=course_dict.get("semester", 1),
            credits=course_dict.get("credits", 0),
            preferred_days=course_dict.get("preferred_days", []),
            preferred_times=course_dict.get("preferred_times", []),
            required_equipment=course_dict.get("required_equipment", []),
            room_type_required=course_dict.get("room_type_required"),
            consecutive_hours=course_dict.get("consecutive_hours", False),
            faculty_preference_score=course_dict.get("faculty_preference_score", 1.0),
            room_preference_score=course_dict.get("room_preference_score", 1.0),
            time_preference_score=course_dict.get("time_preference_score", 1.0)
        )
    
    def _dict_to_room(self, room_dict: Dict) -> Room:
        """Convert dictionary to Room object."""
        return Room(
            id=room_dict.get("id", ""),
            name=room_dict.get("name", ""),
            capacity=room_dict.get("capacity", 0),
            room_type=RoomType(room_dict.get("room_type", "CLASSROOM")),
            building=room_dict.get("building", ""),
            floor=room_dict.get("floor", 1),
            equipment=room_dict.get("equipment", []),
            features=room_dict.get("features", []),
            availability=room_dict.get("availability", None),
            acoustics_rating=room_dict.get("acoustics_rating", 1.0),
            lighting_rating=room_dict.get("lighting_rating", 1.0),
            accessibility_rating=room_dict.get("accessibility_rating", 1.0)
        )
    
    def _dict_to_faculty(self, faculty_dict: Dict) -> Faculty:
        """Convert dictionary to Faculty object."""
        return Faculty(
            id=faculty_dict.get("id", ""),
            name=faculty_dict.get("name", ""),
            department=faculty_dict.get("department", ""),
            email=faculty_dict.get("email", ""),
            max_teaching_hours=faculty_dict.get("max_teaching_hours", 20),
            preferred_days=faculty_dict.get("preferred_days", []),
            preferred_times=faculty_dict.get("preferred_times", []),
            unavailable_slots=faculty_dict.get("unavailable_slots", {}),
            consecutive_classes_preference=faculty_dict.get("consecutive_classes_preference", True),
            break_duration_required=faculty_dict.get("break_duration_required", 1),
            current_teaching_hours=faculty_dict.get("current_teaching_hours", 0),
            assigned_slots=faculty_dict.get("assigned_slots", {})
        )
    
    def _create_sample_data(self):
        """Create sample data with proper compatibility."""
        
        # Sample Rooms (create compatible rooms first)
        self.rooms = [
            Room(
                id="R101", name="Room 101", capacity=150,
                room_type=RoomType.CLASSROOM, building="Main Building", floor=1,
                equipment=["projector", "computer", "whiteboard"], features=["acoustic_panels"],
                acoustics_rating=0.9, lighting_rating=0.8, accessibility_rating=1.0
            ),
            Room(
                id="LAB201", name="Computer Lab 201", capacity=40,
                room_type=RoomType.COMPUTER_LAB, building="Technology Building", floor=2,
                equipment=["computers", "software", "network", "projector"], features=["air_conditioning"],
                acoustics_rating=0.85, lighting_rating=0.9, accessibility_rating=0.8
            ),
            Room(
                id="LAB301", name="Physics Lab 301", capacity=30,
                room_type=RoomType.LAB, building="Science Building", floor=3,
                equipment=["lab_equipment", "safety_gear", "fume_hood"], features=["ventilation"],
                acoustics_rating=0.8, lighting_rating=0.7, accessibility_rating=0.9
            ),
            Room(
                id="SEM101", name="Seminar Room 101", capacity=50,
                room_type=RoomType.SEMINAR_ROOM, building="Main Building", floor=1,
                equipment=["projector", "whiteboard"], features=["conference_setup"],
                acoustics_rating=0.9, lighting_rating=0.8, accessibility_rating=1.0
            )
        ]

        # Sample Courses (ensure they match available room types)
        self.courses = [
            Course(
                id="CS101", name="Introduction to Computer Science", code="CS101",
                duration=2, course_type=CourseType.LECTURE, capacity=120,
                faculty_id="F001", department="Computer Science", semester=1, credits=3,
                preferred_days=["Monday", "Wednesday"], preferred_times=["10:00", "11:00"],
                required_equipment=["projector", "computer"], room_type_required="classroom"
            ),
            Course(
                id="CS102", name="Programming Lab", code="CS102",
                duration=3, course_type=CourseType.LAB, capacity=30,
                faculty_id="F002", department="Computer Science", semester=1, credits=2,
                preferred_days=["Tuesday", "Thursday"], preferred_times=["14:00", "15:00", "16:00"],
                required_equipment=["computers", "software"], room_type_required="computer_lab",
                consecutive_hours=True
            ),
            Course(
                id="MATH201", name="Calculus II", code="MATH201",
                duration=1, course_type=CourseType.LECTURE, capacity=80,
                faculty_id="F003", department="Mathematics", semester=2, credits=4,
                preferred_days=["Monday", "Wednesday", "Friday"], preferred_times=["09:00"],
                required_equipment=["whiteboard"], room_type_required="classroom"
            ),
            Course(
                id="ENG101", name="Technical Writing", code="ENG101",
                duration=1, course_type=CourseType.SEMINAR, capacity=40,
                faculty_id="F005", department="English", semester=1, credits=2,
                preferred_days=["Friday"], preferred_times=["11:00"],
                required_equipment=["projector"], room_type_required="seminar_room"
            )
        ]

        # Sample Faculty
        self.faculty = [
            Faculty(
                id="F001", name="Dr. Alice Smith", department="Computer Science",
                email="alice.smith@university.edu", max_teaching_hours=20,
                preferred_days=["Monday", "Wednesday", "Friday"], preferred_times=["10:00", "11:00"],
                unavailable_slots={"Tuesday": ["08:00", "09:00"]},
                consecutive_classes_preference=True, break_duration_required=1
            ),
            Faculty(
                id="F002", name="Prof. Bob Johnson", department="Computer Science",
                email="bob.johnson@university.edu", max_teaching_hours=18,
                preferred_days=["Tuesday", "Thursday"], preferred_times=["14:00", "15:00", "16:00"],
                unavailable_slots={}, consecutive_classes_preference=False, break_duration_required=1
            ),
            Faculty(
                id="F003", name="Dr. Charlie Nguyen", department="Mathematics",
                email="charlie.nguyen@university.edu", max_teaching_hours=22,
                preferred_days=["Monday", "Wednesday", "Friday"], preferred_times=["09:00", "10:00"],
                unavailable_slots={"Friday": ["08:00"]},
                consecutive_classes_preference=True, break_duration_required=1
            ),
            Faculty(
                id="F004", name="Dr. Diana Evans", department="Physics",
                email="diana.evans@university.edu", max_teaching_hours=15,
                preferred_days=["Thursday"], preferred_times=["13:00", "14:00"],
                unavailable_slots={}, consecutive_classes_preference=True, break_duration_required=1
            ),
            Faculty(
                id="F005", name="Prof. Ethan Kim", department="English",
                email="ethan.kim@university.edu", max_teaching_hours=18,
                preferred_days=["Friday"], preferred_times=["11:00"],
                unavailable_slots={}, consecutive_classes_preference=False, break_duration_required=1
            )
        ]
        
        print(f"✓ Sample data created:")
        print(f"  Courses: {len(self.courses)}")
        print(f"  Rooms: {len(self.rooms)}")
        print(f"  Faculty: {len(self.faculty)}")
    
    def generate_schedule(self) -> Optional[Schedule]:
        """Generate a new schedule using the greedy algorithm with enhanced debugging."""
        try:
            if not self.courses or not self.rooms or not self.faculty:
                raise ValueError("No data loaded. Please load data first.")
            
            print("🔄 Generating schedule...")
            print(f"📊 Debug Info:")
            print(f"   Courses: {len(self.courses)}")
            print(f"   Rooms: {len(self.rooms)}")  
            print(f"   Faculty: {len(self.faculty)}")
            
            # FIX 2: Initialize resource optimizer and constraint solver if not already done
            if self.resource_optimizer is None and self.rooms and self.faculty:
                print("🔧 Initializing resource optimizer...")
                self.resource_optimizer = ResourceOptimizer(self.rooms, self.faculty)
                
            if self.constraint_solver is None and self.courses and self.rooms and self.faculty:
                print("🔧 Initializing constraint solver...")
                self.constraint_solver = ConstraintSolver(self.courses, self.rooms, self.faculty)
            
            # Enhanced debugging - check each course compatibility
            print("\n🔍 Detailed Course-Room Compatibility Check:")
            for course in self.courses:
                print(f"\n📚 Course: {course.code} ({course.name})")
                print(f"   Requires room type: {course.room_type_required}")
                print(f"   Required equipment: {course.required_equipment}")
                print(f"   Capacity needed: {course.capacity}")
                print(f"   Faculty ID: {course.faculty_id}")
                
                # Check each room for this course
                compatible_rooms = []
                for room in self.rooms:
                    print(f"   🏢 Checking Room: {room.name}")
                    print(f"      Room type: {room.room_type.value}")
                    print(f"      Room equipment: {room.equipment}")
                    print(f"      Room capacity: {room.capacity}")
                    
                    # Check room type
                    room_type_match = (not course.room_type_required or 
                                     room.room_type.value == course.room_type_required)
                    print(f"      Room type match: {room_type_match}")
                    
                    # Check capacity
                    capacity_match = room.capacity >= course.capacity
                    print(f"      Capacity match: {capacity_match}")
                    
                    # Check equipment
                    equipment_match = all(eq in room.equipment for eq in course.required_equipment)
                    print(f"      Equipment match: {equipment_match}")
                    
                    if room_type_match and capacity_match and equipment_match:
                        compatible_rooms.append(room.id)
                        print(f"      ✅ COMPATIBLE!")
                    else:
                        print(f"      ❌ NOT COMPATIBLE")
                
                print(f"   📊 Total compatible rooms: {len(compatible_rooms)}")
                if not compatible_rooms:
                    print(f"   ⚠️  WARNING: No compatible rooms found for {course.code}!")
            
            # Check faculty assignment
            print(f"\n👨‍🏫 Faculty Check:")
            for faculty_member in self.faculty:
                assigned_courses = [c for c in self.courses if c.faculty_id == faculty_member.id]
                print(f"   {faculty_member.name} ({faculty_member.id}): {len(assigned_courses)} courses")
                for course in assigned_courses:
                    print(f"      - {course.code}")
            
            print(f"\n🚀 Starting Greedy Scheduler...")
            
            # Initialize scheduler
            scheduler = GreedyScheduler(self.courses, self.rooms, self.faculty)
            
            # Generate schedule with try-catch for detailed error
            try:
                initial_schedule = scheduler.generate_schedule()
            except Exception as scheduler_error:
                print(f"❌ GreedyScheduler failed with error: {scheduler_error}")
                traceback.print_exc()
                return None
            
            if not initial_schedule:
                print("❌ GreedyScheduler returned None!")
                return None
                
            if not hasattr(initial_schedule, 'entries') or not initial_schedule.entries:
                print("❌ GreedyScheduler returned empty schedule (no entries)!")
                print("   This means no valid assignments were found.")
                print("   Common causes:")
                print("   - Room type mismatches")
                print("   - Missing required equipment")
                print("   - Capacity constraints")
                print("   - Faculty availability conflicts")
                print("   - Time slot conflicts")
                return None
            
            print(f"✅ Initial schedule created with {len(initial_schedule.entries)} entries")
            
            # Show what was scheduled
            print(f"\n📋 Successfully Scheduled Courses:")
            for entry in initial_schedule.entries:
                print(f"   - {entry.course.code}: {entry.room.name} on {entry.day} at {entry.time}")
            
            self.current_schedule = initial_schedule
            
            # Calculate metrics
            self._calculate_metrics()
            
            print("✅ Schedule generated successfully!")
            print(f"   Accuracy: {self.metrics['accuracy']:.1f}%")
            print(f"   Scheduled Courses: {len(initial_schedule.entries)}")
            
            return self.current_schedule
            
        except Exception as e:
            print(f"❌ Error generating schedule: {e}")
            traceback.print_exc()
            return None
    
    def optimize_current_schedule(self) -> Optional[Schedule]:
        """Optimize the current schedule for better resource utilization."""
        try:
            if not self.current_schedule:
                raise ValueError("No schedule to optimize. Please generate a schedule first.")
            
            # FIX 3: Check if resource optimizer is available and initialize if needed
            if self.resource_optimizer is None:
                if self.rooms and self.faculty:
                    print("🔧 Initializing resource optimizer for optimization...")
                    self.resource_optimizer = ResourceOptimizer(self.rooms, self.faculty)
                    print("✓ Resource optimizer initialized")
                else:
                    print("❌ Cannot initialize resource optimizer: rooms or faculty data missing")
                    return None
            
            print("🔄 Optimizing schedule...")
            
            # Get initial metrics
            try:
                initial_metrics = self.resource_optimizer.calculate_resource_metrics(self.current_schedule)
            except Exception as metrics_error:
                print(f"⚠️ Warning: Could not calculate initial metrics: {metrics_error}")
                initial_metrics = {}
            
            # Optimize resource allocation
            try:
                optimized_schedule, improvements = self.resource_optimizer.optimize_resource_allocation(
                    self.current_schedule
                )
            except Exception as optimization_error:
                print(f"❌ Resource optimization failed: {optimization_error}")
                traceback.print_exc()
                return None
            
            # Store optimization metrics
            self.last_optimization_metrics = improvements
            
            # Update current schedule
            self.current_schedule = optimized_schedule
            
            # Recalculate metrics
            self._calculate_metrics()
            
            print("✅ Schedule optimized successfully!")
            print("📈 Optimization Results:")
            for key, value in improvements.items():
                print(f"   {key.replace('_', ' ').title()}: +{value:.1f}%")
            
            return self.current_schedule
            
        except Exception as e:
            print(f"❌ Error optimizing schedule: {e}")
            traceback.print_exc()
            return None
    
    def _calculate_metrics(self):
        """Calculate and update performance metrics with improved error handling."""
        if not self.current_schedule:
            return
        
        try:
            # Basic accuracy calculation
            total_courses = len(self.courses)
            scheduled_courses = len(self.current_schedule.entries)
            self.metrics['accuracy'] = (scheduled_courses / total_courses) * 100 if total_courses > 0 else 0
            
            # FIX 4: Improved conflict detection with error handling
            try:
                if hasattr(self.conflict_detector, 'detect'):
                    conflicts = self.conflict_detector.detect(self.current_schedule)
                    if isinstance(conflicts, dict):
                        total_conflicts = sum(len(conflict_list) for conflict_list in conflicts.values())
                    else:
                        total_conflicts = len(conflicts) if conflicts else 0
                else:
                    print("⚠️ ConflictDetector.detect() method not found, skipping conflict analysis")
                    total_conflicts = 0
            except Exception as conflict_error:
                print(f"⚠️ Error in conflict detection: {conflict_error}")
                total_conflicts = 0
            
            max_possible_conflicts = total_courses  # Simplified estimate
            self.metrics['conflicts_eliminated'] = max(0, (1 - total_conflicts / max_possible_conflicts) * 100) if max_possible_conflicts > 0 else 0
            
            # Resource optimization metrics with error handling
            if self.resource_optimizer:
                try:
                    resource_metrics = self.resource_optimizer.calculate_resource_metrics(self.current_schedule)
                    self.metrics['room_utilization_improvement'] = resource_metrics.get('average_room_utilization', 0)
                    self.metrics['constraint_satisfaction'] = resource_metrics.get('overall_efficiency', 0)
                except Exception as resource_error:
                    print(f"⚠️ ResourceOptimizer error: {resource_error}")
                    self.metrics['room_utilization_improvement'] = 0
                    self.metrics['constraint_satisfaction'] = 0
            else:
                self.metrics['room_utilization_improvement'] = 0
                self.metrics['constraint_satisfaction'] = 0
                
        except Exception as e:
            print(f"⚠️ Error calculating metrics: {e}")
            # Set default values
            self.metrics['accuracy'] = 0.0
            self.metrics['conflicts_eliminated'] = 0.0
            self.metrics['room_utilization_improvement'] = 0.0
            self.metrics['constraint_satisfaction'] = 0.0


def main():
    """Main application entry point."""
    try:
        print("🚀 Starting SmartClassGrid...")
        print("=" * 50)
        
        # Create application instance
        app = SmartClassGrid()
        
        # Load data
        app.load_data()
        
        # Launch GUI
        print("\n💻 Launching GUI...")
        gui_app = SchedulingApp(schedule_generator=app)
        gui_app.run()
        
    except KeyboardInterrupt:
        print("\n⚠ Application interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
    finally:
        print("\n👋 SmartClassGrid shutdown complete")


if __name__ == "__main__":
    main()

