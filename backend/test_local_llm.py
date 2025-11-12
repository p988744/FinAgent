#!/usr/bin/env python3
"""
Test script for local LLM and embedding model.

This script tests:
1. Local LLM connection and response
2. Local embedding model connection and embedding generation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from finagent.config import settings
from finagent.document_processing.embeddings import EmbeddingGenerator
from openai import OpenAI


def test_local_llm():
    """Test local LLM connection."""
    print("\n" + "=" * 60)
    print("Testing Local LLM Connection")
    print("=" * 60)

    print(f"\n📋 Configuration:")
    print(f"   Base URL: {settings.local_llm_base_url}")
    print(f"   Model: {settings.local_llm_model}")
    print(f"   API Key: {settings.local_llm_api_key[:10]}...")

    try:
        client = OpenAI(
            base_url=settings.local_llm_base_url,
            api_key=settings.local_llm_api_key
        )

        print(f"\n🔄 Sending test query to {settings.local_llm_model}...")

        response = client.chat.completions.create(
            model=settings.local_llm_model,
            messages=[
                {"role": "user", "content": "請用繁體中文回答：台灣的首都是哪裡？"}
            ],
            temperature=0.0,
            max_tokens=100
        )

        answer = response.choices[0].message.content

        print(f"\n✅ LLM Response:")
        print(f"   {answer}")
        print(f"\n✅ Local LLM connection successful!")

        return True

    except Exception as e:
        print(f"\n❌ Local LLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_local_embedding():
    """Test local embedding model."""
    print("\n" + "=" * 60)
    print("Testing Local Embedding Model")
    print("=" * 60)

    print(f"\n📋 Configuration:")
    print(f"   Base URL: {settings.local_llm_base_url}")
    print(f"   Embedding Model: {settings.local_embedding_model}")
    print(f"   API Key: {settings.local_llm_api_key[:10]}...")

    try:
        generator = EmbeddingGenerator()

        print(f"\n🔄 Generating embeddings for test text...")

        test_text = "玉山銀行因洗錢防制缺失遭金管會裁罰"
        embedding = generator.generate_embedding(test_text)

        print(f"\n✅ Embedding generated successfully!")
        print(f"   Text: {test_text}")
        print(f"   Embedding dimension: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")

        # Test batch generation
        print(f"\n🔄 Testing batch embedding generation...")
        test_texts = [
            "玉山銀行",
            "金融監督管理委員會",
            "洗錢防制"
        ]

        embeddings = generator.generate_embeddings_batch(test_texts)

        print(f"\n✅ Batch embeddings generated successfully!")
        print(f"   Number of texts: {len(test_texts)}")
        print(f"   Number of embeddings: {len(embeddings)}")
        print(f"   Dimensions: {[len(e) for e in embeddings]}")

        return True

    except Exception as e:
        print(f"\n❌ Local embedding test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Local LLM & Embedding Model Test Suite")
    print("=" * 60)

    print(f"\n📋 Settings:")
    print(f"   Chat LLM Provider: {'Local' if settings.use_local_llm else 'OpenAI'}")
    if settings.use_local_llm:
        print(f"     ├─ URL: {settings.local_llm_base_url}")
        print(f"     └─ Model: {settings.local_llm_model}")

    print(f"   Embedding Provider: {'Local' if settings.use_local_embedding else 'OpenAI'}")
    if settings.use_local_embedding:
        embedding_url = settings.local_embedding_base_url or settings.local_llm_base_url
        print(f"     ├─ URL: {embedding_url}{' (shared with LLM)' if not settings.local_embedding_base_url else ''}")
        print(f"     └─ Model: {settings.local_embedding_model}")

    if not settings.use_local_llm and not settings.use_local_embedding:
        print("\n⚠️  Warning: Both USE_LOCAL_LLM and USE_LOCAL_EMBEDDING are False")
        print("   This test is for local models. Set at least one to true.")
        return

    if settings.use_local_llm and not settings.local_llm_model:
        print("\n⚠️  Warning: USE_LOCAL_LLM is True but LOCAL_LLM_MODEL is not set")
        return

    if settings.use_local_embedding and not settings.local_embedding_model:
        print("\n⚠️  Warning: USE_LOCAL_EMBEDDING is True but LOCAL_EMBEDDING_MODEL is not set")
        return

    # Run tests based on configuration
    llm_success = True
    embedding_success = True

    if settings.use_local_llm:
        llm_success = test_local_llm()
    else:
        print("\n⏭️  Skipping LLM test (using OpenAI)")

    if settings.use_local_embedding:
        embedding_success = test_local_embedding()
    else:
        print("\n⏭️  Skipping embedding test (using OpenAI)")

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    if settings.use_local_llm:
        print(f"\n{'✅' if llm_success else '❌'} Local LLM: {'PASSED' if llm_success else 'FAILED'}")
    else:
        print(f"\n⏭️  Local LLM: SKIPPED (using OpenAI)")

    if settings.use_local_embedding:
        print(f"{'✅' if embedding_success else '❌'} Local Embedding: {'PASSED' if embedding_success else 'FAILED'}")
    else:
        print(f"⏭️  Local Embedding: SKIPPED (using OpenAI)")

    tests_run = (settings.use_local_llm or settings.use_local_embedding)
    all_passed = llm_success and embedding_success

    if not tests_run:
        print("\n⚠️  No local models configured. Using OpenAI for all services.")
    elif all_passed:
        print("\n🎉 All enabled tests passed! Your configuration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")

    print()


if __name__ == "__main__":
    main()
