# src/ui/schedule_viewer.py

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, List
import json

class ScheduleViewer:
    """Advanced schedule viewing window with multiple display options."""
    
    def __init__(self, parent, schedule):
        self.parent = parent
        self.schedule = schedule
        self.current_view = "table"
        
        self.setup_window()
        self.create_widgets()
        self.populate_data()
    
    def setup_window(self):
        """Configure the viewer window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Schedule Viewer - SmartClassGrid")
        self.window.geometry("1000x700")
        self.window.minsize(800, 600)
        
        # Make window modal
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1)
    
    def create_widgets(self):
        """Create and arrange the viewer widgets."""
        # Toolbar
        self.create_toolbar()
        
        # Main content area
        self.create_content_area()
        
        # Status bar
        self.create_status_bar()
    
    def create_toolbar(self):
        """Create the toolbar with view options and controls."""
        toolbar_frame = ttk.Frame(self.window)
        toolbar_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # View selection
        ttk.Label(toolbar_frame, text="View:").grid(row=0, column=0, padx=(0, 5))
        
        self.view_var = tk.StringVar(value=self.current_view)
        view_combo = ttk.Combobox(
            toolbar_frame, 
            textvariable=self.view_var,
            values=["table", "grid"],
            state="readonly",
            width=10
        )
        view_combo.grid(row=0, column=1, padx=(0, 20))
        view_combo.bind("<<ComboboxSelected>>", self.change_view)
        
        # Action buttons
        ttk.Button(
            toolbar_frame, 
            text="Refresh", 
            command=self.populate_data
        ).grid(row=0, column=2, padx=5)
        
        ttk.Button(
            toolbar_frame, 
            text="Close", 
            command=self.window.destroy
        ).grid(row=0, column=3, padx=5)
    
    def create_content_area(self):
        """Create the main content display area."""
        # Create notebook for different view tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Table view tab
        self.create_table_view()
        
        # Statistics tab
        self.create_statistics_view()
    
    def create_table_view(self):
        """Create the table view for schedule entries."""
        table_frame = ttk.Frame(self.notebook)
        self.notebook.add(table_frame, text="Schedule Table")
        
        # Create treeview with scrollbars
        columns = ("course", "room", "faculty", "day", "time", "duration")
        self.table_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        # Configure column headings and widths
        column_config = {
            "course": ("Course", 200),
            "room": ("Room", 150),
            "faculty": ("Faculty", 150),
            "day": ("Day", 100),
            "time": ("Time", 80),
            "duration": ("Duration", 80)
        }
        
        for col, (heading, width) in column_config.items():
            self.table_tree.heading(col, text=heading)
            self.table_tree.column(col, width=width, anchor="center")
        
        # Scrollbars
        table_v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table_tree.yview)
        table_h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.table_tree.xview)
        self.table_tree.configure(yscrollcommand=table_v_scrollbar.set, xscrollcommand=table_h_scrollbar.set)
        
        # Grid the treeview and scrollbars
        self.table_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        table_h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Configure grid weights
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
    
    def create_statistics_view(self):
        """Create the statistics view for schedule metrics."""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="Statistics")
        
        # Create text widget for statistics
        self.stats_text = tk.Text(
            stats_frame, 
            wrap=tk.WORD, 
            font=('Consolas', 11),
            padx=10,
            pady=10
        )
        
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient="vertical", command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        # Grid the text widget and scrollbar
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        stats_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid weights
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.rowconfigure(0, weight=1)
    
    def create_status_bar(self):
        """Create the status bar at the bottom."""
        status_frame = ttk.Frame(self.window)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Schedule summary
        if self.schedule and hasattr(self.schedule, 'entries'):
            total_entries = len(self.schedule.entries)
            accuracy = getattr(self.schedule, 'accuracy_score', 0.0)
            self.status_var.set(f"Total entries: {total_entries} | Accuracy: {accuracy:.1f}%")
        else:
            self.status_var.set("No schedule data available")
    
    def populate_data(self):
        """Populate all views with schedule data."""
        try:
            self.populate_table_view()
            self.populate_statistics_view()
        except Exception as e:
            messagebox.showerror("Error", f"Error populating data: {str(e)}")
    
    def populate_table_view(self):
        """Populate the table view with schedule entries."""
        # Clear existing items
        for item in self.table_tree.get_children():
            self.table_tree.delete(item)
        
        # Check if schedule exists and has entries
        if not self.schedule:
            self.table_tree.insert("", "end", values=("No schedule available", "", "", "", "", ""))
            return
        
        if not hasattr(self.schedule, 'entries') or not self.schedule.entries:
            self.table_tree.insert("", "end", values=("No schedule entries found", "", "", "", "", ""))
            return
        
        # Add schedule entries
        for i, entry in enumerate(self.schedule.entries):
            try:
                # Handle different entry types
                if hasattr(entry, 'course'):  # ScheduleEntry object
                    course_name = entry.course.name if hasattr(entry.course, 'name') else str(entry.course)
                    room_name = entry.room.name if hasattr(entry.room, 'name') else str(entry.room)
                    faculty_name = entry.faculty.name if hasattr(entry.faculty, 'name') else str(entry.faculty)
                    day = entry.day
                    time = entry.time
                    duration = f"{entry.duration}h"
                elif isinstance(entry, dict):  # Dictionary format
                    course_name = entry.get('course', {}).get('name', 'Unknown Course')
                    room_name = entry.get('room', {}).get('name', 'Unknown Room')
                    faculty_name = entry.get('faculty', {}).get('name', 'Unknown Faculty')
                    day = entry.get('day', 'Unknown')
                    time = entry.get('time', 'Unknown')
                    duration = f"{entry.get('duration', 0)}h"
                else:
                    # Fallback for other formats
                    course_name = f"Entry {i+1}"
                    room_name = "Unknown"
                    faculty_name = "Unknown"
                    day = "Unknown"
                    time = "Unknown"
                    duration = "Unknown"
                
                self.table_tree.insert("", "end", values=(
                    course_name,
                    room_name,
                    faculty_name,
                    day,
                    time,
                    duration
                ))
                
            except Exception as e:
                # Handle individual entry errors
                self.table_tree.insert("", "end", values=(
                    f"Error in entry {i+1}",
                    str(e),
                    "",
                    "",
                    "",
                    ""
                ))
    
    def populate_statistics_view(self):
        """Populate the statistics view with schedule metrics."""
        self.stats_text.delete(1.0, tk.END)
        
        try:
            # Check if schedule exists
            if not self.schedule:
                self.stats_text.insert(tk.END, "No schedule data available.")
                return
            
            self.stats_text.insert(tk.END, "SMARTCLASSGRID SCHEDULE STATISTICS\n")
            self.stats_text.insert(tk.END, "=" * 50 + "\n\n")
            
            # Basic statistics
            if hasattr(self.schedule, 'entries') and self.schedule.entries:
                entry_count = len(self.schedule.entries)
                self.stats_text.insert(tk.END, f"📊 OVERVIEW\n")
                self.stats_text.insert(tk.END, f"Total Schedule Entries: {entry_count}\n")
                
                if hasattr(self.schedule, 'accuracy_score'):
                    self.stats_text.insert(tk.END, f"Scheduling Accuracy: {self.schedule.accuracy_score:.1f}%\n")
                
                if hasattr(self.schedule, 'total_conflicts'):
                    self.stats_text.insert(tk.END, f"Total Conflicts: {self.schedule.total_conflicts}\n")
                
                # Course distribution
                courses = set()
                rooms = set()
                faculty = set()
                days = {}
                
                for entry in self.schedule.entries:
                    try:
                        if hasattr(entry, 'course'):
                            courses.add(entry.course.name if hasattr(entry.course, 'name') else str(entry.course))
                            rooms.add(entry.room.name if hasattr(entry.room, 'name') else str(entry.room))
                            faculty.add(entry.faculty.name if hasattr(entry.faculty, 'name') else str(entry.faculty))
                            day = entry.day
                            days[day] = days.get(day, 0) + 1
                    except:
                        continue
                
                self.stats_text.insert(tk.END, f"\n📚 RESOURCE USAGE\n")
                self.stats_text.insert(tk.END, f"Unique Courses: {len(courses)}\n")
                self.stats_text.insert(tk.END, f"Rooms Used: {len(rooms)}\n")
                self.stats_text.insert(tk.END, f"Faculty Involved: {len(faculty)}\n")
                
                self.stats_text.insert(tk.END, f"\n📅 DAILY DISTRIBUTION\n")
                for day, count in sorted(days.items()):
                    self.stats_text.insert(tk.END, f"  {day}: {count} classes\n")
                
            else:
                self.stats_text.insert(tk.END, "No schedule entries to analyze.\n")
                
        except Exception as e:
            self.stats_text.insert(tk.END, f"Error generating statistics: {str(e)}\n")
    
    def change_view(self, event=None):
        """Change the current view mode."""
        self.current_view = self.view_var.get()
        # Additional view switching logic can be added here
    
    def sort_table(self, column):
        """Sort table by column."""
        try:
            items = [(self.table_tree.set(child, column), child) for child in self.table_tree.get_children('')]
            items.sort()
            
            for index, (_, child) in enumerate(items):
                self.table_tree.move(child, '', index)
        except Exception as e:
            messagebox.showerror("Sort Error", f"Could not sort table: {str(e)}")

