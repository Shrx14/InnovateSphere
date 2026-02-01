import json
from generation.generator import mock_llm_generate
from generation.schemas import validate_generated_idea

# Test the mock
prompt = 'dummy prompt'
raw_output = mock_llm_generate(prompt)
parsed = json.loads(raw_output)
validated_idea = validate_generated_idea(parsed)
print('Mock generation passes schema validation: SUCCESS')
print(f'Number of evidence sources: {len(validated_idea.evidence_sources)}')
print(f'Source types: {set(s.source_type for s in validated_idea.evidence_sources)}')
