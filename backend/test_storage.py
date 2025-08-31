#!/usr/bin/env python3
"""Test script for the storage system."""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.services.storage_service import StorageService
from app.models.storage import ChatRecord


async def test_storage():
    """Test the storage system."""
    print("🧪 Testing Storage System...")
    
    # Create a test storage service
    storage = StorageService("test_data")
    
    # Test 1: Create a session
    print("\n1. Creating a session...")
    session = storage.create_session("Test Chat Session")
    print(f"   ✅ Created session: {session.session_id}")
    print(f"   ✅ Title: {session.title}")
    
    # Test 2: Store a chat record
    print("\n2. Storing chat records...")
    record1 = storage.store_chat_record(
        user_text="Hello, how are you?",
        response_text="I'm doing well, thank you! How can I help you today?",
        session_id=session.session_id
    )
    print(f"   ✅ Stored record 1")
    
    record2 = storage.store_chat_record(
        user_text="What's the weather like?",
        response_text="I don't have access to real-time weather data, but I can help you find weather information if you'd like.",
        session_id=session.session_id
    )
    print(f"   ✅ Stored record 2")
    
    # Test 3: Retrieve session records
    print("\n3. Retrieving session records...")
    records = storage.get_session_records(session.session_id)
    print(f"   ✅ Found {len(records)} records")
    
    for i, record in enumerate(records, 1):
        print(f"   Record {i}:")
        print(f"     User: {record.user_input.text}")
        print(f"     Assistant: {record.response.text}")
        print(f"     Session: {record.user_input.chat_session}")
        print(f"     Timestamp: {record.user_input.timestamp}")
    
    # Test 4: Search records
    print("\n4. Searching records...")
    search_results = storage.search_records("weather")
    print(f"   ✅ Found {len(search_results)} records containing 'weather'")
    
    # Test 5: Get all sessions
    print("\n5. Getting all sessions...")
    all_sessions = storage.get_all_sessions()
    print(f"   ✅ Found {len(all_sessions)} sessions")
    
    # Test 6: Get storage stats
    print("\n6. Getting storage statistics...")
    stats = storage.get_stats()
    print(f"   ✅ Total records: {stats['total_records']}")
    print(f"   ✅ Total sessions: {stats['total_sessions']}")
    print(f"   ✅ Storage directory: {stats['storage_dir']}")
    
    # Test 7: Verify JSON structure
    print("\n7. Verifying JSON structure...")
    if records:
        record = records[0]
        print("   Sample JSON structure:")
        json_data = record.model_dump()
        
        print("   {")
        print(f"     \"user_input\": {{")
        print(f"       \"timestamp\": \"{json_data['user_input']['timestamp']}\",")
        print(f"       \"text\": \"{json_data['user_input']['text']}\",")
        print(f"       \"chat_session\": \"{json_data['user_input']['chat_session']}\"")
        print(f"     }},")
        print(f"     \"response\": {{")
        print(f"       \"timestamp\": \"{json_data['response']['timestamp']}\",")
        print(f"       \"text\": \"{json_data['response']['text']}\",")
        print(f"       \"chat_session\": \"{json_data['response']['chat_session']}\"")
        print(f"     }}")
        print("   }")
    
    print("\n✅ All tests completed successfully!")
    
    # Cleanup test data
    print("\n🧹 Cleaning up test data...")
    import shutil
    shutil.rmtree("test_data", ignore_errors=True)
    print("   ✅ Test data cleaned up")


if __name__ == "__main__":
    asyncio.run(test_storage())
