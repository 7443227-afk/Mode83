#!/usr/bin/env python3
"""
Test script for database functionality
"""

import sys
import os

# Add the parent directory to the path so we can import the database module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import init_database, create_tables, add_assertion, get_assertion_by_id, import_assertions_from_directory, sync_assertion_record
import uuid
import json

def test_database():
    """Test the database functionality"""
    print("Testing database functionality...")
    
    # Initialize database
    db_path = "badge83/data/test_registry.db"
    conn = init_database(db_path)
    
    # Create tables
    create_tables(conn)
    print("Database initialized successfully")
    
    # Test data
    test_data = {
        'assertion_id': 'test-assertion-' + str(uuid.uuid4())[:8],
        'assertion_data': {'name': 'Test Badge', 'issuer': 'Test Issuer'},
        'issued_on': '2026-04-23',
        'name': 'Test User',
        'email': 'test@example.com',
        'name_hash': 'hashed_name',
        'email_hash': 'hashed_email'
    }
    
    # Add test assertion
    assertion_id = add_assertion(conn, test_data)
    print(f"Added assertion with ID: {assertion_id}")
    
    # Retrieve assertion
    result = get_assertion_by_id(conn, test_data['assertion_id'])
    if result:
        print("Successfully retrieved assertion:")
        print(result)
    else:
        print("Failed to retrieve assertion")
    
    sample_json_path = os.path.join("badge83", "data", f"{test_data['assertion_id']}.json")
    with open(sample_json_path, "w", encoding="utf-8") as handle:
        json.dump({
            "id": f"https://mode83.local/assertions/{test_data['assertion_id']}",
            "type": "Assertion",
            "issuedOn": test_data["issued_on"],
            "admin_recipient": {"name": test_data["name"], "email": test_data["email"]},
            "search": {"name_hash": test_data["name_hash"], "email_hash": test_data["email_hash"]},
        }, handle)

    sync_assertion_record(test_data['assertion_id'], {
        "id": f"https://mode83.local/assertions/{test_data['assertion_id']}",
        "type": "Assertion",
        "issuedOn": test_data["issued_on"],
        "admin_recipient": {"name": test_data["name"], "email": test_data["email"]},
        "search": {"name_hash": test_data["name_hash"], "email_hash": test_data["email_hash"]},
    }, db_path)
    import_stats = import_assertions_from_directory("badge83/data", db_path)
    print(f"Import stats: {import_stats}")

    # Close connection
    conn.close()
    
    # Clean up test database
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Test database removed")
    if os.path.exists(sample_json_path):
        os.remove(sample_json_path)
    
    print("Database test completed")

if __name__ == "__main__":
    test_database()