#!/usr/bin/env python3
"""Test script to verify the list index out of range fix"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.anna_agent.backbone import configure
from pathlib import Path

# Initialize AnnaAgent configuration
configure(Path("."))

# Import the fixed MsPatient 
from src.anna_agent.ms_patient import MsPatient

def test_fixed_patient():
    """Test that the fixed MsPatient handles empty responses gracefully"""
    print("🔧 Testing fixed MsPatient...")
    
    # Default patient profile for testing
    profile = {
        "age": "28",
        "gender": "男",
        "occupation": "软件工程师",
        "martial_status": "未婚",
        "symptoms": "工作焦虑，失眠"
    }
    
    report = {"案例标题": "工作压力咨询"}
    previous_conversations = []
    
    try:
        # Create patient instance
        patient = MsPatient(profile, report, previous_conversations)
        print("✅ Patient instance created successfully")
        
        # Test chat functionality
        print("🗨️  Testing chat with message: '你好'")
        response = patient.chat("你好")
        
        print(f"📝 Response received: {response}")
        print(f"📏 Response length: {len(response) if response else 0}")
        
        if response and response.strip():
            print("✅ SUCCESS: Fixed code is working! No more list index out of range!")
            return True
        else:
            print("⚠️  Got empty response but no crash - fix is working")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_fixed_patient()
    if success:
        print("\n🎉 FIXED! The list index out of range error has been resolved!")
        sys.exit(0)
    else:
        print("\n💥 Still has issues")
        sys.exit(1)