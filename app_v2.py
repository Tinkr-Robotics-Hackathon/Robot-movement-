import asyncio
import json
import os
import sys
import math
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

# Position data for all chess squares with forward distances and rotation angles
POSITION_DATA = {
    # Column A (left edge, 90 degrees left rotation)
    "a8": {"forward": 30, "rotation": -90},
    "a7": {"forward": 70, "rotation": -90},
    "a6": {"forward": 120, "rotation": -90},
    "a5": {"forward": 150, "rotation": -90},
    "a4": {"forward": 180, "rotation": -90},
    "a3": {"forward": 210, "rotation": -90},
    "a2": {"forward": 240, "rotation": -90},
    "a1": {"forward": 270, "rotation": -90},
    
    # Column B (45 degrees left rotation)
    "b8": {"forward": 42, "rotation": -45},
    "b7": {"forward": 98, "rotation": -45},
    "b6": {"forward": 169, "rotation": -45},
    "b5": {"forward": 212, "rotation": -45},
    "b4": {"forward": 254, "rotation": -45},
    "b3": {"forward": 297, "rotation": -45},
    "b2": {"forward": 339, "rotation": -45},
    "b1": {"forward": 382, "rotation": -45},
    
    # Column C (22 degrees left rotation)
    "c8": {"forward": 32, "rotation": -22},
    "c7": {"forward": 76, "rotation": -22},
    "c6": {"forward": 130, "rotation": -22},
    "c5": {"forward": 163, "rotation": -22},
    "c4": {"forward": 195, "rotation": -22},
    "c3": {"forward": 228, "rotation": -22},
    "c2": {"forward": 260, "rotation": -22},
    "c1": {"forward": 292, "rotation": -22},
    
    # Column D (no rotation, robot aligned)
    "d8": {"forward": 30, "rotation": 0},
    "d7": {"forward": 70, "rotation": 0},
    "d6": {"forward": 120, "rotation": 0},
    "d5": {"forward": 150, "rotation": 0},
    "d4": {"forward": 180, "rotation": 0},
    "d3": {"forward": 210, "rotation": 0},
    "d2": {"forward": 240, "rotation": 0},
    "d1": {"forward": 270, "rotation": 0},
    
    # Column E (22 degrees right rotation)
    "e8": {"forward": 32, "rotation": 22},
    "e7": {"forward": 76, "rotation": 22},
    "e6": {"forward": 130, "rotation": 22},
    "e5": {"forward": 163, "rotation": 22},
    "e4": {"forward": 195, "rotation": 22},
    "e3": {"forward": 228, "rotation": 22},
    "e2": {"forward": 260, "rotation": 22},
    "e1": {"forward": 292, "rotation": 22},
    
    # Column F (45 degrees right rotation)
    "f8": {"forward": 42, "rotation": 45},
    "f7": {"forward": 98, "rotation": 45},
    "f6": {"forward": 169, "rotation": 45},
    "f5": {"forward": 212, "rotation": 45},
    "f4": {"forward": 254, "rotation": 45},
    "f3": {"forward": 297, "rotation": 45},
    "f2": {"forward": 339, "rotation": 45},
    "f1": {"forward": 382, "rotation": 45},
    
    # Column G (67 degrees right rotation)
    "g8": {"forward": 78, "rotation": 67},
    "g7": {"forward": 179, "rotation": 67},
    "g6": {"forward": 307, "rotation": 67},
    "g5": {"forward": 384, "rotation": 67},
    "g4": {"forward": 461, "rotation": 67},
    "g3": {"forward": 538, "rotation": 67},
    "g2": {"forward": 614, "rotation": 67},
    "g1": {"forward": 691, "rotation": 67},
    
    # Column H (90 degrees right rotation)
    "h8": {"forward": 30, "rotation": 90},
    "h7": {"forward": 70, "rotation": 90},
    "h6": {"forward": 120, "rotation": 90},
    "h5": {"forward": 150, "rotation": 90},
    "h4": {"forward": 180, "rotation": 90},
    "h3": {"forward": 210, "rotation": 90},
    "h2": {"forward": 240, "rotation": 90},
    "h1": {"forward": 270, "rotation": 90},
}

async def execute_robot_sequence(sequence):
    """Execute a sequence of robot movements using MCP server."""
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_robot_server.py", "--transport", "stdio"],
        env=os.environ,
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                for step in sequence:
                    if "wait" in step:
                        wait_time = step["wait"]
                        print(f"⏳ Waiting for {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        tool_name = step["tool"]
                        tool_args = step["args"]

                        print(f"🔧 Executing: {tool_name} with args {tool_args}")
                        result = await session.call_tool(tool_name, arguments=tool_args)
                        print(f"✅ Result: {result}")

                    await asyncio.sleep(0.3)  # Small delay between steps

    except Exception as e:
        print(f"❌ Error executing sequence: {e}")
        raise

def create_home_sequence(forward_distance, rotation_angle):
    """Generate home sequence with specified forward distance and rotation reset."""
    rotation_reset = -rotation_angle if rotation_angle != 0 else 0
    
    home_sequence = [   
        {"tool": "move_robot", "args": {"move_gripper_up_mm": "50"}},
        {"tool": "move_robot", "args": {"tilt_gripper_down_angle": "-80"}},
        {"tool": "move_robot", "args": {"move_gripper_up_mm": "-75"}},
        {"tool": "move_robot", "args": {"move_gripper_forward_mm": f"-{forward_distance}"}}
    ]
    
    # Add rotation reset if needed
    if rotation_reset != 0:
        home_sequence.append({"tool": "move_robot", "args": {"rotate_robot_right_angle": str(rotation_reset)}})
    
    return home_sequence

async def execute_command_sequence(command_name, commands):
    """Execute a specific command from the JSON file."""
    if command_name not in commands:
        print(f"❌ Error: Command '{command_name}' not found in JSON")
        return
    
    print(f"\n🎯 --- Executing: {command_name.upper()} ---")
    await execute_robot_sequence(commands[command_name])

def validate_position(position):
    """Validate chess position format and availability."""
    if len(position) != 2:
        return False, "Invalid position format. Use format like 'd7', 'e5', etc."
    
    if position[0] not in 'abcdefgh':
        return False, f"Invalid column '{position[0]}'. Must be a-h."
    
    if position[1] not in '12345678':
        return False, f"Invalid row '{position[1]}'. Must be 1-8."
    
    if position not in POSITION_DATA:
        return False, f"Position '{position}' not available in position data."
    
    return True, "Valid"

async def move_chess_piece(from_position, to_position):
    """
    Execute complete chess piece movement following the exact sequence:
    attack → open → from_position → close → home → attack → to_position → open → home → close → move_for_cam
    """
    
    # Load command sequences from JSON
    try:
        with open('command.json', 'r') as file:
            commands = json.load(file)
    except FileNotFoundError:
        print("❌ Error: command.json file not found")
        return
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON format in command.json")
        return
    
    # Validate positions exist in commands
    if from_position not in commands:
        print(f"❌ Error: Position '{from_position}' not found in commands.json")
        return
    
    if to_position not in commands:
        print(f"❌ Error: Position '{to_position}' not found in commands.json")
        return
    
    # Get position data
    from_data = POSITION_DATA[from_position]
    to_data = POSITION_DATA[to_position]
    
    print(f"🚀 Starting chess move: {from_position.upper()} → {to_position.upper()}")
    print("=" * 70)
    print(f"📍 From position: {from_position.upper()} (Forward: {from_data['forward']}mm, Rotation: {from_data['rotation']}°)")
    print(f"📍 To position: {to_position.upper()} (Forward: {to_data['forward']}mm, Rotation: {to_data['rotation']}°)")
    print("=" * 70)
    
    try:
        # STEP 1: Attack position
        await execute_command_sequence("attack", commands)
        
        # STEP 2: Open gripper (prepare for picking)
        await execute_command_sequence("open", commands)
        
        # STEP 3: Move to source position
        await execute_command_sequence(from_position, commands)
        
        # STEP 4: Close gripper (pick up piece)
        await execute_command_sequence("close", commands)
        
        # STEP 5: Home (return to home with piece)
        print(f"\n🏠 --- Executing: HOME (from {from_position.upper()}) ---")
        home_sequence = create_home_sequence(from_data["forward"], from_data["rotation"])
        await execute_robot_sequence(home_sequence)
        
        # STEP 6: Attack position (again)
        await execute_command_sequence("attack", commands)
        
        # STEP 7: Move to destination position
        await execute_command_sequence(to_position, commands)
        
        # STEP 8: Open gripper (drop piece)
        await execute_command_sequence("open", commands)
        
        # STEP 9: Home (return to home position)
        print(f"\n🏠 --- Executing: HOME (from {to_position.upper()}) ---")
        home_sequence = create_home_sequence(to_data["forward"], to_data["rotation"])
        await execute_robot_sequence(home_sequence)
        
        # STEP 10: Close gripper (final position)
        await execute_command_sequence("close", commands)
        
        # STEP 11: Move for camera
        await execute_command_sequence("move_for_cam", commands)
        
        print(f"\n🎉 Successfully completed chess move: {from_position.upper()} → {to_position.upper()}")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error during chess move: {e}")
        raise

def print_usage():
    """Print comprehensive usage instructions."""
    print("🏛️  Chess Robot Controller")
    print("=" * 50)
    print("📋 Usage: python app.py <from_position> <to_position>")
    print("📋 Example: python app.py d7 d5")
    print("\n📍 Available positions (all 64 squares):")
    
    # Print positions in a chess board layout
    rows = ['8', '7', '6', '5', '4', '3', '2', '1']
    cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    
    for row in rows:
        row_positions = [f"{col}{row}" for col in cols]
        print(f"   {row}: {' '.join(row_positions)}")
    
    print("\n🔄 Movement sequence executed:")
    print("   1. attack → 2. open → 3. from_position → 4. close → 5. home")
    print("   6. attack → 7. to_position → 8. open → 9. home → 10. close → 11. move_for_cam")
    
    print("\n🎯 Robot configuration:")
    print("   • Board: 260mm x 260mm (33mm per square)")
    print("   • Robot: SO-101 with 6 DOF")
    print("   • Position: 2cm from D column edge")
    print("   • Rotation: Automatic based on target column")

def print_position_info(position):
    """Print detailed information about a specific position."""
    if position in POSITION_DATA:
        data = POSITION_DATA[position]
        print(f"\n📍 Position {position.upper()} details:")
        print(f"   Forward distance: {data['forward']}mm")
        print(f"   Rotation angle: {data['rotation']}°")
        column = position[0]
        if data['rotation'] == 0:
            print(f"   Column {column.upper()}: Direct alignment (no rotation)")
        elif data['rotation'] < 0:
            print(f"   Column {column.upper()}: Left rotation")
        else:
            print(f"   Column {column.upper()}: Right rotation")

async def main():
    """Main function to handle command line arguments and execute chess move."""
    
    # Check command line arguments
    if len(sys.argv) != 3:
        print("❌ Error: Invalid number of arguments\n")
        print_usage()
        return
    
    from_position = sys.argv[1].lower()
    to_position = sys.argv[2].lower()
    
    # Validate positions
    from_valid, from_msg = validate_position(from_position)
    if not from_valid:
        print(f"❌ Error: From position - {from_msg}\n")
        print_usage()
        return
        
    to_valid, to_msg = validate_position(to_position)
    if not to_valid:
        print(f"❌ Error: To position - {to_msg}\n")
        print_usage()
        return
    
    # Check if positions are the same
    if from_position == to_position:
        print("❌ Error: From and to positions cannot be the same\n")
        return
    
    print("🤖 Chess Robot Controller - Move Execution")
    print("=" * 50)
    print_position_info(from_position)
    print_position_info(to_position)
    print("\n🎯 Executing move sequence...")
    print("=" * 50)
    
    # Execute the chess move
    await move_chess_piece(from_position, to_position)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Move interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
