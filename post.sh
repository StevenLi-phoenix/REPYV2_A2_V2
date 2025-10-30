REMOTE_URL="http://100.88.83.27:8000"

curl -X POST $REMOTE_URL/execute \
  -H "Content-Type: application/json" \
  -d '{"monitor_text": "log(\"test\")\n", "attack_text": "log(\"attack\")\n"}'