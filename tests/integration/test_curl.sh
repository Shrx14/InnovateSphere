#!/bin/bash
# Test the API directly with curl

url="http://localhost:5000/api/ideas/generate"
auth="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3MDY1NTg1OCwianRpIjoiZmJhYWMzZjQtZTVhMi00ODUzLThkZTUtODBjMmMxYjI1ZWUwIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6OCwibmJmIjoxNzcwNjU1ODU4LCJleHAiOjE3NzA2NTY3NTgsInJvbGUiOiJ1c2VyIiwiZW1haWwiOiJ0ZXN0QHRlc3QuY29tIiwicHJlZmVycmVkX2RvbWFpbl9pZCI6bnVsbH0.Ytr7Fh5u0xEfCnz9bMkATQWDiGJUH4n2NHVi24QlJLU"

payload='{"query": "Machine learning personalized recommendation system", "domain_id": 1}'

curl -X POST "$url" \
  -H "Authorization: $auth" \
  -H "Content-Type: application/json" \
  -d "$payload" \
  -s | jq .

