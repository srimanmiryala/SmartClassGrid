

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


from src.main import SmartClassGrid, SchedulingApp

def main():
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
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

