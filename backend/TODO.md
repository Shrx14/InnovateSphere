# TODO: Fix schemas.py and generator.py based on feedback

## Tasks
- [x] Edit schemas.py: Replace @validator('*') with @root_validator for evidence references validation
- [x] Edit generator.py: Update mock_llm_generate to include >=4 evidence_sources with >=2 distinct source_types
- [x] Edit generator.py: Improve novelty text construction using "\n".join with formatted strings
- [x] Verify that mock generation passes schema validation end-to-end
