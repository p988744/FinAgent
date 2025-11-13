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


def test_llm():
    """Test LLM connection."""
    print("\n" + "=" * 60)
    print("Testing LLM Connection")
    print("=" * 60)

    base_url = settings.effective_llm_base_url
    print(f"\n📋 Configuration:")
    print(f"   Provider: {'Custom endpoint' if base_url else 'OpenAI'}")
    if base_url:
        print(f"   Base URL: {base_url}")
    print(f"   Model: {settings.llm_model}")
    print(f"   API Key: {settings.effective_llm_api_key[:10]}...")

    try:
        if base_url:
            client = OpenAI(
                base_url=base_url,
                api_key=settings.effective_llm_api_key
            )
        else:
            client = OpenAI(
                api_key=settings.effective_llm_api_key
            )

        print(f"\n🔄 Sending test query to {settings.llm_model}...")

        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "user", "content": "請用繁體中文回答：台灣的首都是哪裡？"}
            ],
            temperature=0.0,
            max_tokens=100
        )

        answer = response.choices[0].message.content

        print(f"\n✅ LLM Response:")
        print(f"   {answer}")
        print(f"\n✅ LLM connection successful!")

        return True

    except Exception as e:
        print(f"\n❌ LLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embedding():
    """Test embedding model."""
    print("\n" + "=" * 60)
    print("Testing Embedding Model")
    print("=" * 60)

    base_url = settings.effective_embedding_base_url
    print(f"\n📋 Configuration:")
    print(f"   Provider: {'Custom endpoint' if base_url else 'OpenAI'}")
    if base_url:
        print(f"   Base URL: {base_url}")
    print(f"   Embedding Model: {settings.embedding_model}")
    print(f"   API Key: {settings.effective_embedding_api_key[:10]}...")

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
        print(f"\n❌ Embedding test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("LLM & Embedding Model Test Suite")
    print("=" * 60)

    llm_base_url = settings.effective_llm_base_url
    embedding_base_url = settings.effective_embedding_base_url

    print(f"\n📋 Settings:")
    print(f"   Chat LLM Provider: {'Custom endpoint' if llm_base_url else 'OpenAI'}")
    if llm_base_url:
        print(f"     ├─ URL: {llm_base_url}")
    print(f"     └─ Model: {settings.llm_model}")

    print(f"   Embedding Provider: {'Custom endpoint' if embedding_base_url else 'OpenAI'}")
    if embedding_base_url:
        shared = embedding_base_url == llm_base_url
        print(f"     ├─ URL: {embedding_base_url}{' (shared with LLM)' if shared else ''}")
    print(f"     └─ Model: {settings.embedding_model}")

    # Run tests
    llm_success = test_llm()
    embedding_success = test_embedding()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    print(f"\n{'✅' if llm_success else '❌'} LLM: {'PASSED' if llm_success else 'FAILED'}")
    print(f"{'✅' if embedding_success else '❌'} Embedding: {'PASSED' if embedding_success else 'FAILED'}")

    all_passed = llm_success and embedding_success

    if all_passed:
        print("\n🎉 All tests passed! Your configuration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")

    print()


if __name__ == "__main__":
    main()
