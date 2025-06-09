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
SERVER_URL = 'https://www.pumpplaysosrs.xyz'

# Game window coordinates - UPDATED WITH YOUR ACTUAL OSRS WINDOW!
GAME_WINDOW = {
    'x': 0,        # Fullscreen starts at top-left of monitor
    'y': 0,        # No title bar in fullscreen
    'width': 1920, # Full monitor width
    'height': 1080 # Full monitor height
}

CLICK_OFFSET_X = 0  # No offset needed for fullscreen
CLICK_OFFSET_Y = 0

# Safety settings
pyautogui.PAUSE = 0.1  # Pause between actions
pyautogui.FAILSAFE = True  # Move mouse to top-left corner to stop

# Create socket client
sio = socketio.Client(logger=False, engineio_logger=False)

def execute_arrow_key(direction):
    """Execute arrow key press for camera movement - FIXED FOR OSRS"""
    try:
        # Ensure OSRS window is focused first
        focus_osrs_window()
        
        # OSRS uses different keys for camera rotation!
        # Arrow keys don't work in OSRS - need to use mouse for camera
        # Let's simulate mouse drag for camera movement instead
        
        if direction == 'up':
            # Mouse drag up for camera pitch
            start_x = GAME_WINDOW['x'] + GAME_WINDOW['width'] // 2
            start_y = GAME_WINDOW['y'] + GAME_WINDOW['height'] // 2
            pyautogui.drag(0, -50, duration=0.3, button='middle')
        elif direction == 'down':
            pyautogui.drag(0, 50, duration=0.3, button='middle')
        elif direction == 'left':
            # Mouse drag left for camera yaw
            pyautogui.drag(-50, 0, duration=0.3, button='middle')
        elif direction == 'right':
            pyautogui.drag(50, 0, duration=0.3, button='middle')
        else:
            print(f"❌ Unknown direction: {direction}")
            return False
            
        print(f"✅ Camera moved: {direction}")
        return True
            
    except Exception as e:
        print(f"❌ Error with camera movement {direction}: {e}")
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

def execute_right_click(rel_x, rel_y):
    """Execute right click for context menus"""
    try:
        abs_x = GAME_WINDOW['x'] + (rel_x * GAME_WINDOW['width']) + CLICK_OFFSET_X
        abs_y = GAME_WINDOW['y'] + (rel_y * GAME_WINDOW['height']) + CLICK_OFFSET_Y
        
        focus_osrs_window()
        time.sleep(0.1)
        
        # Move mouse first, then right click
        pyautogui.moveTo(abs_x, abs_y, duration=0.1)
        time.sleep(0.05)
        
        pyautogui.rightClick(abs_x, abs_y)
        print(f"✅ Right click at ({abs_x:.0f}, {abs_y:.0f}) - rel: {rel_x:.3f}, {rel_y:.3f}")
        
        time.sleep(0.2)
        return True
        
    except Exception as e:
        print(f"❌ Error with right click: {e}")
        return False

def execute_direct_click(rel_x, rel_y):
    """Execute direct click on game window at exact coordinates"""
    try:
        # Convert relative coordinates (0-1) to absolute screen coordinates
        abs_x = GAME_WINDOW['x'] + (rel_x * GAME_WINDOW['width']) + CLICK_OFFSET_X
        abs_y = GAME_WINDOW['y'] + (rel_y * GAME_WINDOW['height']) + CLICK_OFFSET_Y
        
        # CRITICAL: Ensure OSRS window is focused and active
        focus_osrs_window()
        time.sleep(0.1)  # Give focus time to take effect
        
        # Move mouse to position first (helps with object detection)
        pyautogui.moveTo(abs_x, abs_y, duration=0.1)
        time.sleep(0.05)  # Brief pause for OSRS to detect mouse hover
        
        # Execute the click with proper timing for object interaction
        pyautogui.click(abs_x, abs_y, duration=0.05)
        print(f"✅ Direct click at ({abs_x:.0f}, {abs_y:.0f}) - rel: {rel_x:.3f}, {rel_y:.3f}")
        
        time.sleep(0.2)  # Longer delay for OSRS object recognition
        return True
        
    except Exception as e:
        print(f"❌ Error with direct click: {e}")
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
                
        elif action == 'right_click':
            # Handle right clicks for context menus
            x = data.get('x')
            y = data.get('y')
            if x is not None and y is not None:
                success = execute_right_click(x, y)
            else:
                error_msg = "Invalid right click coordinates"
                
        elif action == 'direct_click':
            # Handle direct clicks on the stream (exact coordinates)
            x = data.get('x')
            y = data.get('y')
            if x is not None and y is not None:
                success = execute_direct_click(x, y)
            else:
                error_msg = "Invalid direct click coordinates"
                
        elif action == 'stream_click':
            # Handle clicks on stream overlay (legacy support)
            zone = data.get('zone')
            x = data.get('x')
            y = data.get('y')
            if zone and x is not None and y is not None:
                success = execute_direct_click(x, y)  # Use same function now
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

def focus_osrs_window():
    """Ensure OSRS window is focused for proper object interaction"""
    try:
        # For fullscreen OSRS, just click in a safe area to ensure focus
        # Click on the center of the screen briefly
        center_x = GAME_WINDOW['x'] + (GAME_WINDOW['width'] // 2)
        center_y = GAME_WINDOW['y'] + (GAME_WINDOW['height'] // 2)
        
        # Quick focus click in game area (won't interfere with gameplay)
        current_pos = pyautogui.position()
        pyautogui.click(center_x, center_y)
        time.sleep(0.02)  # Very brief pause
        
        # Move mouse back to original position
        pyautogui.moveTo(current_pos[0], current_pos[1], duration=0.05)
        
    except Exception as e:
        print(f"⚠️ Could not focus OSRS window: {e}")

def calibrate_coordinates():
    """Interactive calibration system to map stream coordinates to game coordinates"""
    print("🎯 COORDINATE CALIBRATION SYSTEM")
    print("=" * 50)
    print("This will help map your stream clicks to exact game positions.")
    print("You'll click 6 reference points on your OSRS window.")
    print()
    
    calibration_points = []
    
    # Define the calibration sequence
    calibration_sequence = [
        ("TOP-LEFT corner of game area", "Click the very top-left corner of your OSRS game area"),
        ("TOP-RIGHT corner of game area", "Click the very top-right corner of your OSRS game area"),
        ("BOTTOM-LEFT corner of game area", "Click the very bottom-left corner of your OSRS game area"),
        ("BOTTOM-RIGHT corner of game area", "Click the very bottom-right corner of your OSRS game area"),
        ("FIRST INVENTORY SLOT", "Click the first inventory slot (top-left of inventory)"),
        ("A SPECIFIC ITEM", "Click on any item in your inventory that you can see clearly")
    ]
    
    print("🖱️  INSTRUCTIONS:")
    print("- Position your mouse over each point when prompted")
    print("- Press SPACE when your mouse is exactly on the target")
    print("- Press ESC to cancel calibration")
    print()
    
    for i, (point_name, instruction) in enumerate(calibration_sequence):
        print(f"📍 STEP {i+1}/6: {point_name}")
        print(f"   {instruction}")
        print("   Position mouse and press SPACE when ready...")
        
        # Wait for user input
        while True:
            try:
                # Get current mouse position
                x, y = pyautogui.position()
                print(f"\r   Mouse: ({x}, {y}) - Press SPACE when positioned correctly...", end="", flush=True)
                
                # Check for keyboard input (simplified - just wait for Enter)
                import msvcrt
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b' ':  # Space bar
                        calibration_points.append((point_name, x, y))
                        print(f"\n   ✅ Recorded: {point_name} at ({x}, {y})")
                        break
                    elif key == b'\x1b':  # Escape
                        print("\n❌ Calibration cancelled.")
                        return None
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n❌ Calibration cancelled.")
                return None
        
        print()
    
    # Calculate the calibration data
    print("🧮 Calculating calibration...")
    
    # Extract coordinates
    top_left = calibration_points[0][1:3]      # x, y
    top_right = calibration_points[1][1:3]
    bottom_left = calibration_points[2][1:3]
    bottom_right = calibration_points[3][1:3]
    inventory_first = calibration_points[4][1:3]
    test_item = calibration_points[5][1:3]
    
    # Calculate game area bounds
    game_left = min(top_left[0], bottom_left[0])
    game_right = max(top_right[0], bottom_right[0])
    game_top = min(top_left[1], top_right[1])
    game_bottom = max(bottom_left[1], bottom_right[1])
    
    game_width = game_right - game_left
    game_height = game_bottom - game_top
    
    # Calculate where inventory and test item are relative to game area
    inv_rel_x = (inventory_first[0] - game_left) / game_width
    inv_rel_y = (inventory_first[1] - game_top) / game_height
    
    test_rel_x = (test_item[0] - game_left) / game_width
    test_rel_y = (test_item[1] - game_top) / game_height
    
    print("✅ Calibration Complete!")
    print("=" * 50)
    print("📊 RESULTS:")
    print(f"Game Area: ({game_left}, {game_top}) to ({game_right}, {game_bottom})")
    print(f"Game Size: {game_width} x {game_height}")
    print(f"First Inventory Slot: {inv_rel_x:.3f}, {inv_rel_y:.3f} (relative)")
    print(f"Test Item Position: {test_rel_x:.3f}, {test_rel_y:.3f} (relative)")
    print()
    
    # Generate the new GAME_WINDOW configuration
    print("🔧 UPDATE YOUR pc_client.py WITH THESE VALUES:")
    print("=" * 50)
    print("GAME_WINDOW = {")
    print(f"    'x': {game_left},")
    print(f"    'y': {game_top},")
    print(f"    'width': {game_width},")
    print(f"    'height': {game_height}")
    print("}")
    print()
    print("# No offset needed with proper calibration!")
    print("CLICK_OFFSET_X = 0")
    print("CLICK_OFFSET_Y = 0")
    print()
    
    # Test the calibration
    print("🧪 TESTING CALIBRATION:")
    print("Testing click on your inventory first slot in 3 seconds...")
    time.sleep(3)
    
    # Update the global GAME_WINDOW temporarily
    global GAME_WINDOW
    old_window = GAME_WINDOW.copy()
    GAME_WINDOW.update({
        'x': game_left,
        'y': game_top,
        'width': game_width,
        'height': game_height
    })
    
    # Test click on inventory
    execute_direct_click(inv_rel_x, inv_rel_y)
    print(f"   Should have clicked first inventory slot!")
    
    time.sleep(2)
    
    # Test click on the item they selected
    execute_direct_click(test_rel_x, test_rel_y)
    print(f"   Should have clicked your test item!")
    
    # Restore old window settings
    GAME_WINDOW = old_window
    
    print()
    print("✅ If those clicks were accurate, update your GAME_WINDOW values!")
    print("   If not, run calibration again.")
    
    return {
        'game_window': {
            'x': game_left,
            'y': game_top, 
            'width': game_width,
            'height': game_height
        },
        'inventory_first': (inv_rel_x, inv_rel_y),
        'test_item': (test_rel_x, test_rel_y)
    }
    """Debug function to see exactly where clicks land"""
    print("🔍 Debug mode: Click test in 3 seconds...")
    print("Watch your inventory area carefully!")
    time.sleep(3)
    
    # Test click on what should be the logs position
    # Based on your screenshot, logs appear to be around 25% from left, 65% from top
    logs_x = 0.25  # 25% from left edge
    logs_y = 0.65  # 65% from top edge
    
    print(f"Testing click at logs position: {logs_x}, {logs_y}")
    execute_direct_click(logs_x, logs_y)
    
    time.sleep(2)
    
    # Test a few other positions to see the pattern
    test_positions = [
        (0.2, 0.6, "Left of logs"),
        (0.3, 0.6, "Right of logs"), 
        (0.25, 0.55, "Above logs"),
        (0.25, 0.7, "Below logs")
    ]
    
    for x, y, desc in test_positions:
        print(f"Testing {desc}: {x}, {y}")
        execute_direct_click(x, y)
        time.sleep(1)
    
    print("🔍 Debug test complete! Check where each click landed.")
    """Test function to check if clicks are accurate"""
    print("🧪 Testing coordinate accuracy...")
    print("Click test will happen in 3 seconds - watch your OSRS window!")
    time.sleep(3)
    
    # Test clicks at different positions
    test_positions = [
        (0.1, 0.1, "Top-left area"),
        (0.5, 0.5, "Center"),
        (0.9, 0.9, "Bottom-right area"),
        (0.25, 0.75, "Inventory area (if visible)")
    ]
    
    for rel_x, rel_y, description in test_positions:
        print(f"Testing {description}...")
        execute_direct_click(rel_x, rel_y)
        time.sleep(1)
    
    print("✅ Coordinate test complete!")
    print("💡 If clicks are still off, adjust CLICK_OFFSET_X and CLICK_OFFSET_Y")

def get_mouse_position():
    """Test function to check if clicks are accurate"""
    print("🧪 Testing coordinate accuracy...")
    print("Click test will happen in 3 seconds - watch your OSRS window!")
    time.sleep(3)
    
    # Test clicks at different positions
    test_positions = [
        (0.1, 0.1, "Top-left area"),
        (0.5, 0.5, "Center"),
        (0.9, 0.9, "Bottom-right area"),
        (0.25, 0.75, "Inventory area (if visible)")
    ]
    
    for rel_x, rel_y, description in test_positions:
        print(f"Testing {description}...")
        execute_direct_click(rel_x, rel_y)
        time.sleep(1)
    
    print("✅ Coordinate test complete!")
    print("💡 If clicks are still off, adjust CLICK_OFFSET_X and CLICK_OFFSET_Y")
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
        elif sys.argv[1] == 'simple':
            print("🎯 Starting simple calibration...")
            simple_calibrate()
        elif sys.argv[1] == 'calibrate':
            print("🎯 Starting coordinate calibration...")
            calibrate_coordinates()
        elif sys.argv[1] == 'debug':
            print("🔍 Debug click positions...")
            debug_click_position()
        elif sys.argv[1] == 'coords':
            print("🎯 Testing coordinate accuracy...")
            test_coordinate_accuracy()
        elif sys.argv[1] == 'help':
            print("🎮 cow714 OSRS PC Client")
            print("Usage:")
            print("  python pc_client.py        - Run the client")
            print("  python pc_client.py test   - Test commands")
            print("  python pc_client.py mouse  - Get mouse coordinates")
            print("  python pc_client.py simple    - Simple calibration (recommended)")
            print("  python pc_client.py calibrate - Interactive coordinate calibration")
            print("  python pc_client.py debug   - Debug inventory clicking")
            print("  python pc_client.py coords  - Test coordinate accuracy")
            print("  python pc_client.py help   - Show this help")
        else:
            print("❌ Unknown command. Use 'help' for usage.")
    else:
        main()
