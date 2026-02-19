#!/usr/bin/env python3
"""
Test script for Pokemon Ability API
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    print("=" * 50)
    print("Testing Health Check Endpoint")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_process_ability():
    """Test process ability endpoint"""
    print("=" * 50)
    print("Testing Process Ability Endpoint")
    print("=" * 50)
    
    test_data = {
        "raw_id": "7dsa8d7sa9dsa",
        "user_id": "5199434",
        "pokemon_ability_id": "150"
    }
    
    print(f"Sending request with data:")
    print(json.dumps(test_data, indent=2))
    print()
    
    response = requests.post(
        f"{BASE_URL}/process-ability",
        json=test_data
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))
    print()

def test_retrieve_abilities():
    """Test retrieve abilities endpoint"""
    print("=" * 50)
    print("Testing Retrieve Abilities Endpoint")
    print("=" * 50)
    
    raw_id = "7dsa8d7sa9dsa"
    user_id = "5199434"
    
    response = requests.get(f"{BASE_URL}/abilities/{raw_id}/{user_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))
    print()

def test_multiple_abilities():
    """Test with different Pokemon abilities"""
    print("=" * 50)
    print("Testing Multiple Pokemon Abilities")
    print("=" * 50)
    
    test_cases = [
        {"raw_id": "abc1234567890", "user_id": "1234567", "pokemon_ability_id": "1"},   # Stench
        {"raw_id": "def0987654321", "user_id": "9876543", "pokemon_ability_id": "65"},  # Overgrow
        {"raw_id": "ghi5555555555", "user_id": "5555555", "pokemon_ability_id": "150"}, # Impostor (Ditto)
    ]
    
    for i, test_data in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Pokemon Ability ID: {test_data['pokemon_ability_id']}")
        
        response = requests.post(
            f"{BASE_URL}/process-ability",
            json=test_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success")
            print(f"  Pokemon: {', '.join(data['pokemon_list'][:3])}{'...' if len(data['pokemon_list']) > 3 else ''}")
            print(f"  Total Pokemon: {len(data['pokemon_list'])}")
            print(f"  Languages: {len(data['returned_entries'])}")
        else:
            print(f"✗ Failed: {response.status_code}")
        
        time.sleep(0.5)  # Rate limiting
    
    print()

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Pokemon Ability API Test Suite")
    print("=" * 50 + "\n")
    
    try:
        # Run tests
        test_health_check()
        test_process_ability()
        test_retrieve_abilities()
        test_multiple_abilities()
        
        print("=" * 50)
        print("All tests completed!")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API. Make sure the server is running at", BASE_URL)
    except Exception as e:
        print(f"Error: {str(e)}")
