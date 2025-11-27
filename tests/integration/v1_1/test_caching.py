"""Integration test for caching."""

import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from finagent.document_processing.retriever import DocumentRetriever

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run the caching test."""
    print("🚀 Starting Caching Test")
    
    # Initialize retriever
    retriever = DocumentRetriever(collection_name="legal_documents")
    
    query = "What is AML?"
    
    print("\n1️⃣ First Query (Uncached)...")
    start_time = time.time()
    retriever.retrieve(query)
    duration1 = time.time() - start_time
    print(f"Duration: {duration1:.4f} seconds")
    
    print("\n2️⃣ Second Query (Cached)...")
    start_time = time.time()
    retriever.retrieve(query)
    duration2 = time.time() - start_time
    print(f"Duration: {duration2:.4f} seconds")
    
    # Check if second query is faster
    # Note: In a real environment, network latency might fluctuate, but caching should be significantly faster
    # because it skips the embedding generation call.
    
    if duration2 < duration1:
        print(f"\n✅ Caching works! Speedup: {duration1/duration2:.2f}x")
    else:
        print("\n⚠️ Caching might not be working or network fluctuation masked it.")
        print(f"First: {duration1}, Second: {duration2}")

    # Verify cache info if possible
    if hasattr(retriever._get_query_embedding, "cache_info"):
        info = retriever._get_query_embedding.cache_info()
        print(f"\nCache Info: {info}")
        if info.hits >= 1:
             print("✅ Cache hits confirmed.")
        else:
             print("❌ No cache hits.")

if __name__ == "__main__":
    main()
