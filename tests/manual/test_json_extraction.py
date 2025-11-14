#!/usr/bin/env python3
"""Test JSON extraction from markdown code blocks."""

import re
import json

# Test the regex extraction with markdown code blocks
test_response = """```json
{
  "document_type": "裁罰書",
  "issuing_authority": "金融監督管理委員會",
  "penalty_amount": "新臺幣2億5千萬元"
}
```"""

print("Test response:")
print(test_response)
print()

# Current regex (matches only {...})
json_match = re.search(r'\{.*\}', test_response, re.DOTALL)
if json_match:
    print("Extracted JSON:")
    extracted = json_match.group(0)
    print(extracted)
    print()
    data = json.loads(extracted)
    print("✅ Parsed successfully!")
    print(json.dumps(data, ensure_ascii=False, indent=2))
