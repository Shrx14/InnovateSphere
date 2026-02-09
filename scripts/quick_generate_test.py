import sys
sys.path.insert(0, 'd:\\Work\\InnovateSphere')
from backend.ai.llm_client import generate_json

print('Calling generate_json with a tiny prompt...')
try:
    out = generate_json('Please return {"status":"ok","echo":"pong"} as JSON only')
    print('Result type:', type(out))
    print(out)
except Exception as e:
    print('Error:', type(e), e)
