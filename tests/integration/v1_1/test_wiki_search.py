"""Integration test for the Wiki Search agent flow."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from finagent.agents.wiki_search.graph import WikiSearchWorkflow
from finagent.document_processing.retriever import DocumentRetriever
from finagent.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Run the integration test."""
    print("🚀 Starting Wiki Search Agent Test")
    
    # Initialize dependencies
    retriever = DocumentRetriever(collection_name="legal_documents")
    
    # Initialize workflow
    workflow = WikiSearchWorkflow(retriever=retriever)
    
    # Test query
    query = "什麼是洗錢防制法？"
    print(f"\n❓ Query: {query}\n")
    
    # Run workflow
    initial_state = {
        "input": query,
        "documents": [],
        "response": ""
    }
    
    try:
        # Stream the execution
        async for event in workflow.graph.astream(initial_state):
            for key, value in event.items():
                print(f"\n📍 Node: {key}")
                if key == "search":
                    docs = value["documents"]
                    print(f"🔎 Found {len(docs)} documents.")
                    for i, doc in enumerate(docs[:2]): # Show first 2
                        print(f"  - [{i+1}] {doc.metadata.get('filename', 'Unknown')}")
                elif key == "synthesize":
                    print("\n✨ Final Response:")
                    print(value["response"])
                            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
