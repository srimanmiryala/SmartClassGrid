# src/models/__init__.py

"""
Data Models Module

Contains all data model classes for courses, rooms, faculty, and schedules.
"""

from .course import Course, CourseType
from .room import Room, RoomType
from .faculty import Faculty
from .schedule import Schedule, ScheduleEntry

__all__ = [
    'Course',
    'CourseType',
    'Room', 
    'RoomType',
    'Faculty',
    'Schedule',
    'ScheduleEntry'
]

