#!/usr/bin/env python3
"""Test if the LLM endpoint is working correctly."""

from openai import OpenAI
from finagent.config import settings, reload_settings

# Reload settings
reload_settings()

print("=" * 80)
print("Testing LLM Endpoint Configuration")
print("=" * 80)
print()
print(f"LLM Base URL: {settings.effective_llm_base_url}")
print(f"LLM Model: {settings.llm_model}")
print(f"LLM API Key: {settings.effective_llm_api_key[:20]}..." if settings.effective_llm_api_key else "None")
print()

# Initialize client
if settings.effective_llm_base_url:
    client = OpenAI(
        api_key=settings.effective_llm_api_key,
        base_url=settings.effective_llm_base_url
    )
else:
    client = OpenAI(api_key=settings.effective_llm_api_key)

print("=" * 80)
print("Test 1: Simple completion")
print("=" * 80)

try:
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": "你是一個有幫助的助手。"},
            {"role": "user", "content": "請回答：1+1等於多少？"}
        ],
        temperature=0.0,
    )

    result = response.choices[0].message.content
    print(f"✅ Success!")
    print(f"Response: {result}")
    print()

except Exception as e:
    print(f"❌ Failed: {e}")
    print()

print("=" * 80)
print("Test 2: JSON output (with response_format)")
print("=" * 80)

try:
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": "你是一個有幫助的助手。請以JSON格式回答。"},
            {"role": "user", "content": '請以JSON格式回答：{"answer": "你的答案"}。問題：台灣的首都是哪裡？'}
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    result = response.choices[0].message.content
    print(f"✅ Success!")
    print(f"Response: {result}")
    print()

except Exception as e:
    print(f"❌ Failed: {e}")
    print(f"Error type: {type(e).__name__}")
    print()

    # Try without response_format
    print("Retrying without response_format parameter...")
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "你是一個有幫助的助手。請以JSON格式回答。"},
                {"role": "user", "content": '請以JSON格式回答：{"answer": "你的答案"}。問題：台灣的首都是哪裡？'}
            ],
            temperature=0.0,
        )

        result = response.choices[0].message.content
        print(f"✅ Success without response_format!")
        print(f"Response: {result}")
        print()

    except Exception as e2:
        print(f"❌ Also failed without response_format: {e2}")
        print()

print("=" * 80)
print("Test 3: Metadata extraction (realistic)")
print("=" * 80)

test_content = """金融監督管理委員會 裁罰書

受處分人：玉山商業銀行股份有限公司
地址：台北市松山區民生東路三段115號
統一編號：03782905

案由：
玉山商業銀行股份有限公司因洗錢防制及打擊資恐作業缺失，經本會審酌後，依銀行法第129條第7款規定，處新臺幣2億5千萬元罰鍰。

事實：
一、未能有效辨識客戶身分
二、未能妥適評估客戶風險
三、未能及時申報可疑交易

依據：銀行法第129條第7款
"""

try:
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": "你是一個專業的法律文件分析助手。請以JSON格式回傳分析結果。"},
            {"role": "user", "content": f"""請分析以下文件並以JSON格式回傳元資料：

{test_content}

請回傳JSON格式：
{{
  "document_type": "裁罰書或判決書或其他",
  "issuing_authority": "發布機關",
  "penalty_amount": "罰鍰金額"
}}
"""}
        ],
        temperature=0.0,
    )

    result = response.choices[0].message.content
    print(f"✅ Success!")
    print(f"Response length: {len(result)} chars")
    print(f"Response: {result}")
    print()

    # Try to parse as JSON
    import json
    try:
        data = json.loads(result)
        print(f"✅ Valid JSON!")
        print(f"Parsed: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except json.JSONDecodeError as je:
        print(f"❌ Not valid JSON: {je}")
        print(f"Trying to extract JSON from response...")
        import re
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                print(f"✅ Extracted and parsed JSON!")
                print(f"Parsed: {json.dumps(data, ensure_ascii=False, indent=2)}")
            except:
                print(f"❌ Still not valid JSON")

except Exception as e:
    print(f"❌ Failed: {e}")
    print()

print("=" * 80)
print("Test Complete")
print("=" * 80)
