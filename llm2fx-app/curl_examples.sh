# Example cURL request for testing the API

# Start the server first:
# bash run.sh

# Then test with cURL:
curl -s -X POST http://localhost:8000/text2fx \
  -H "Content-Type: application/json" \
  -d '{"fx_type":"reverb","instrument":"vocal","instruction":"warm small room"}' | jq .

# Alternative without jq:
curl -s -X POST http://localhost:8000/text2fx \
  -H "Content-Type: application/json" \
  -d '{"fx_type":"reverb","instrument":"vocal","instruction":"warm small room"}'

# Test health endpoint:
curl -s http://localhost:8000/healthz
