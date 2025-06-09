#!/usr/bin/env python3
"""
PC Client for cow714 OSRS Community Controller
Run this on your gaming PC to receive commands from Heroku
"""

import socketio
import pyautogui
import time
from pynput import keyboard
from pynput.keyboard import Key
import sys

# Your Heroku app URL - UPDATE THIS WITH YOUR ACTUAL HEROKU APP NAME!
SERVER_URL = 'https://cow714-osrs-controller-221dee6aaaf8.herokuapp.com/'

# Game window coordinates - ADJUST THESE FOR YOUR SETUP!
# Use 'python pc_client.py mouse' to help find these coordinates
GAME_WINDOW = {
    'x': 100,      # Left edge of your OSRS window
    'y': 100,      # Top edge of your OSRS window  
    'width': 800,  # Width of your OSRS window
    'height': 600  # Height of your OSRS window
}

# Safety settings
pyautogui.PAUSE = 0.1  # Pause between actions
pyautogui.FAILSAFE = True  # Move mouse to top-left corner to stop

# Create socket client
sio = socketio.Client(logger=False, engineio_logger=False)

def execute_arrow_key(direction):
    """Execute arrow key press for camera movement"""
    try:
        key_map = {
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right
        }
        
        if direction in key_map:
            with keyboard.Controller() as kb:
                kb.press(key_map[direction])
                time.sleep(0.05)  # Brief hold
                kb.release(key_map[direction])
            print(f"✅ Arrow key: {direction}")
            return True
        else:
            print(f"❌ Unknown arrow key: {direction}")
            return False
            
    except Exception as e:
        print(f"❌ Error with arrow key {direction}: {e}")
        return False

def execute_click(click_type, x=None, y=None):
    """Execute mouse click"""
    try:
        if click_type == "left-click":
            if x is not None and y is not None:
                pyautogui.click(x, y)
                print(f"✅ Left click at ({x}, {y})")
            else:
                pyautogui.click()
                print("✅ Left click at current position")
                
        elif click_type == "right-click":
            if x is not None and y is not None:
                pyautogui.rightClick(x, y)
                print(f"✅ Right click at ({x}, {y})")
            else:
                pyautogui.rightClick()
                print("✅ Right click at current position")
        else:
            print(f"❌ Unknown click type: {click_type}")
            return False
            
        time.sleep(0.1)  # Prevent spam
        return True
        
    except Exception as e:
        print(f"❌ Error with click {click_type}: {e}")
        return False

def execute_stream_click(zone, rel_x, rel_y):
    """Execute click on stream overlay zone"""
    try:
        # Convert relative coordinates to absolute screen coordinates
        abs_x = GAME_WINDOW['x'] + (rel_x * GAME_WINDOW['width'])
        abs_y = GAME_WINDOW['y'] + (rel_y * GAME_WINDOW['height'])
        
        # Execute the click
        pyautogui.click(abs_x, abs_y)
        print(f"✅ Stream zone '{zone}' clicked at ({abs_x:.0f}, {abs_y:.0f})")
        
        time.sleep(0.1)
        return True
        
    except Exception as e:
        print(f"❌ Error with stream click: {e}")
        return False

@sio.event
def connect():
    """Called when connected to server"""
    print("🎮 Connected to cow714 OSRS controller!")
    print(f"📡 Server: {SERVER_URL}")
    
    # Register as PC client
    sio.emit('register_pc')

@sio.event  
def disconnect():
    """Called when disconnected from server"""
    print("❌ Disconnected from server")

@sio.on('pc_registered')
def on_registered(data):
    """Called when PC registration is confirmed"""
    print("✅ PC client registered successfully!")
    print("🎯 Ready to receive commands from viewers...")

@sio.on('execute_command')
def on_command(command_data):
    """Handle commands from web interface"""
    try:
        action = command_data.get('action')
        data = command_data.get('data', {})
        user_id = command_data.get('userId', 'unknown')
        
        print(f"🎯 Command from {user_id[:8]}...: {action}")
        
        success = False
        error_msg = None
        
        if action == 'key_press':
            # Handle arrow key presses
            key = data.get('key')
            if key in ['up', 'down', 'left', 'right']:
                success = execute_arrow_key(key)
            else:
                error_msg = f"Unknown key: {key}"
                
        elif action == 'action':
            # Handle click actions
            action_type = data.get('type')
            if action_type in ['left-click', 'right-click']:
                success = execute_click(action_type)
            else:
                error_msg = f"Unknown action type: {action_type}"
                
        elif action == 'stream_click':
            # Handle clicks on stream overlay
            zone = data.get('zone')
            x = data.get('x')
            y = data.get('y')
            if zone and x is not None and y is not None:
                success = execute_stream_click(zone, x, y)
            else:
                error_msg = "Invalid stream click data"
                
        else:
            error_msg = f"Unknown command action: {action}"
        
        # Send completion status back to server
        if success:
            sio.emit('command_completed', {
                'command': command_data,
                'status': 'success',
                'timestamp': time.time()
            })
        else:
            print(f"❌ {error_msg}")
            sio.emit('command_completed', {
                'command': command_data,
                'status': 'error',
                'error': error_msg,
                'timestamp': time.time()
            })
            
    except Exception as e:
        print(f"❌ Error processing command: {e}")
        sio.emit('command_completed', {
            'command': command_data,
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        })

def get_mouse_position():
    """Utility function to help find game window coordinates"""
    print("🖱️  Position your OSRS window, then move mouse to find coordinates:")
    print("   1. Move to TOP-LEFT corner of game area")
    print("   2. Move to BOTTOM-RIGHT corner of game area")
    print("   3. Press Ctrl+C when done")
    print()
    
    try:
        while True:
            x, y = pyautogui.position()
            print(f"\rMouse position: ({x}, {y})    ", end="", flush=True)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"\n📍 Final position: ({x}, {y})")
        print("\nTo set up GAME_WINDOW:")
        print("1. Top-left corner = x, y values")
        print("2. Width = right_edge - left_edge")
        print("3. Height = bottom_edge - top_edge")
        return x, y

def test_commands():
    """Test function to verify everything works"""
    print("🧪 Testing commands in 3 seconds...")
    print("Make sure OSRS is in focus!")
    time.sleep(3)
    
    # Test arrow keys
    print("Testing arrow keys...")
    for direction in ['up', 'down', 'left', 'right']:
        execute_arrow_key(direction)
        time.sleep(0.5)
    
    # Test clicks
    print("Testing clicks...")
    execute_click('left-click')
    time.sleep(0.5)
    execute_click('right-click')
    
    print("✅ Test complete!")

def check_dependencies():
    """Check if all required packages are installed"""
    try:
        import pyautogui
        import socketio
        from pynput import keyboard
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install with: pip install python-socketio[client] pyautogui pynput")
        return False

def main():
    """Main function"""
    print("🚀 cow714 OSRS PC Client Starting...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        input("Press Enter to exit...")
        return
    
    print(f"📡 Server: {SERVER_URL}")
    print("⚙️  Game window settings:")
    print(f"   Position: ({GAME_WINDOW['x']}, {GAME_WINDOW['y']})")
    print(f"   Size: {GAME_WINDOW['width']}x{GAME_WINDOW['height']}")
    print()
    
    # Check if server URL needs to be updated
    if 'cow714-osrs-controller' not in SERVER_URL:
        print("⚠️  WARNING: Please update SERVER_URL with your Heroku app name!")
        print("   Edit this file and change the SERVER_URL to match your Heroku app")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    print("🎮 Starting connection...")
    print("💡 Tips:")
    print("   - Make sure your OSRS client is positioned correctly")
    print("   - Run 'python pc_client.py mouse' to find coordinates")
    print("   - Run 'python pc_client.py test' to test inputs")
    print("   - Move mouse to top-left corner to emergency stop")
    print()
    
    try:
        # Connect to server
        print("🔌 Connecting to Heroku...")
        sio.connect(SERVER_URL)
        print("✅ Connected! Waiting for commands from viewers...")
        print("🎯 cow714's OSRS is now community controlled!")
        
        # Keep the client running
        sio.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure your Heroku app is running")
        print("2. Check the SERVER_URL is correct")
        print("3. Verify your internet connection")
        print("4. Try: heroku logs --tail")
        input("\nPress Enter to exit...")

if __name__ == '__main__':
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            print("🧪 Testing mode...")
            test_commands()
        elif sys.argv[1] == 'mouse':
            print("🖱️  Mouse coordinate finder...")
            get_mouse_position()
        elif sys.argv[1] == 'help':
            print("🎮 cow714 OSRS PC Client")
            print("Usage:")
            print("  python pc_client.py        - Run the client")
            print("  python pc_client.py test   - Test commands")
            print("  python pc_client.py mouse  - Get mouse coordinates")
            print("  python pc_client.py help   - Show this help")
        else:
            print("❌ Unknown command. Use 'help' for usage.")
    else:
        main()
