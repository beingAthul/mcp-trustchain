import json
import httpx
import argparse
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def load_json(filepath: str):
    with open(filepath, 'r') as f:
        return json.load(f)

def run_simulation(filepath: str, tool_id: str):
    print(f"\n--- MCP Client Simulation for Tool: {tool_id} ---\n")
    print(f"1. Loading Config: {filepath}")
    
    try:
        config = load_json(filepath)
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    print("2. Requesting execution verification from MCPGuard...")
    
    try:
        response = httpx.post(f"{BASE_URL}/verify", json={
            "tool_id": tool_id,
            "config": config
        })
        
        data = response.json()
        
        print("\n--- Integrity Verification Result ---")
        print(f"Decision: {data.get('decision')}")
        print(f"Reason:   {data.get('reason')}")
        print(f"Match:    {data.get('match')}")
        
        if data.get('decision') == 'ALLOW':
            print("\n[✓] MCP Client executing tool...")
            # actual execution would happen here
        else:
            print("\n[✗] MCP Client denied execution by MCPGuard.")
            
    except Exception as e:
        print(f"Verification request failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate an MCP Client")
    parser.add_argument("config_file", help="Path to mcp.json")
    parser.add_argument("tool_id", help="Registered Tool ID")
    
    args = parser.parse_args()
    
    config_path = Path(__args.config_file)
    if not config_path.exists():
        print(f"File not found: {args.config_file}")
        sys.exit(1)
        
    run_simulation(args.config_file, args.tool_id)
