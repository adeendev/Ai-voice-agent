#!/usr/bin/env python3
"""
Test script to verify timezone conversion fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import pytz
from vertiqx_voice_agent import VertiqxReceptionistAgent

def test_timezone_conversion():
    """Test that time parsing works correctly with local timezone"""
    
    print("🧪 Testing Timezone Conversion Fix")
    print("=" * 50)
    
    # Initialize the voice agent (without audio components for testing)
    try:
        agent = VertiqxReceptionistAgent()
        print("✅ Voice agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize voice agent: {e}")
        return False
    
    # Test cases for time parsing
    test_cases = [
        "4 PM",
        "4:00 PM", 
        "16:00",
        "2 PM",
        "10 AM",
        "6:30 PM"
    ]
    
    print("\n📅 Testing Time Parsing:")
    print("-" * 30)
    
    for time_str in test_cases:
        try:
            # Test the _parse_datetime method
            parsed_dt = agent._parse_datetime(time_str)
            
            if parsed_dt:
                print(f"Input: '{time_str}'")
                print(f"  → Parsed: {parsed_dt}")
                print(f"  → Timezone: {parsed_dt.tzinfo}")
                print(f"  → Local time: {parsed_dt.strftime('%I:%M %p %Z')}")
                print()
            else:
                print(f"❌ Failed to parse: '{time_str}'")
                
        except Exception as e:
            print(f"❌ Error parsing '{time_str}': {e}")
    
    print("✅ Timezone conversion test completed!")
    return True

if __name__ == "__main__":
    test_timezone_conversion()