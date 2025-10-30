#!/usr/bin/env python3
"""
Test script for the FastAPI server.
Run this after starting the server with: uvicorn app:app --reload
"""
import requests
import json
import pprint
import argparse
base_url = "http://100.88.83.27:8000"


def post(monitor_text, attack_text):
    response = requests.get(f"{base_url}/health")
    assert response.status_code == 200
    payload = {
        "monitor_text": monitor_text,
        "attack_text": attack_text
    }
    response = requests.post(f"{base_url}/execute", json=payload)
    assert response.status_code == 200
    return response.json()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--monitor-text", type=str, default="sample_monitor.py")
    parser.add_argument("--attack-text", type=str, default="sample_attack.py")
    return parser.parse_args()

def main():
    args = parse_args()
    result = post(open(args.monitor_text).read(), open(args.attack_text).read())
    print(result)

if __name__ == "__main__":
    main()