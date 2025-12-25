import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def print_separator():
    print("-" * 40)

def main():
    print("HTTP Client Demo")
    print_separator()

    print("Creating function 'sum_sq': f(x, y) = x^2 + y^2")
    payload = {
        "name": "sum_sq",
        "inputs": ["x", "y"],
        "outputs": ["z"],
        "expression": "x**2 + y**2"
    }
    resp = requests.post(f"{BASE_URL}/functions", json=payload)
    print(f"Status: {resp.status_code}, Response: {resp.json()}")
    print_separator()

    print("Listing functions:")
    resp = requests.get(f"{BASE_URL}/functions")
    print(resp.json())
    print_separator()

    print("Executing 'sum_sq' with x=3, y=4")
    exec_payload = {"args": {"x": 3, "y": 4}}
    resp = requests.post(f"{BASE_URL}/functions/sum_sq/execute", json=exec_payload)
    print(f"Result: {resp.json()}")
    print_separator()

    print("Updating 'sum_sq' to be x + y")
    update_payload = {
        "name": "sum_sq",
        "inputs": ["x", "y"],
        "outputs": ["z"],
        "expression": "x + y"
    }
    resp = requests.put(f"{BASE_URL}/functions/sum_sq", json=update_payload)
    print(f"Update Status: {resp.status_code}")
    
    print("Executing updated 'sum_sq' with x=3, y=4")
    resp = requests.post(f"{BASE_URL}/functions/sum_sq/execute", json=exec_payload)
    print(f"Result: {resp.json()}")
    print_separator()

    print("Deleting 'sum_sq'")
    resp = requests.delete(f"{BASE_URL}/functions/sum_sq")
    print(f"Delete Status: {resp.status_code}")
    print_separator()

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure server.py is running.")

