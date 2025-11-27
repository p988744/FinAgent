"""
Unit tests for LLM connection using vanilla OpenAI and LangGraph v1.0.

Purpose: Verify LLM gateway connection stability and performance.

Best Practices Applied:
1. Environment Configuration & Tracing
2. Error Handling & Retry Logic
3. State Management & Validation
4. Observability & Monitoring
5. Connection Testing Strategy
"""

import asyncio
import time
from typing import TypedDict, Annotated
from operator import add

# Vanilla OpenAI client
import openai

# LangChain v1.0 imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# LangGraph v1.0 imports
from langgraph.graph import StateGraph, START, END

# Load configuration
from finagent.config_manager import ConfigManager


class TestState(TypedDict):
    """State for LangGraph test (using TypedDict for type safety)."""
    messages: Annotated[list, add]
    test_result: str
    execution_time: float


def test_vanilla_openai_connection():
    """
    Test 1: Vanilla OpenAI client connection test.

    Purpose: Verify basic OpenAI API connectivity without LangChain overhead.
    """
    print("\n" + "=" * 80)
    print("TEST 1: Vanilla OpenAI Connection Test")
    print("=" * 80)

    # Load configuration
    config = ConfigManager()
    settings = config.get_all_settings()

    api_key = settings.get("llm_api_key")
    base_url = settings.get("llm_base_url")
    model = settings.get("llm_model", "gpt-4o-mini")

    print(f"API Key: {api_key[:20]}..." if api_key else "API Key: Not set")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print("-" * 80)

    try:
        # Create OpenAI client
        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=10.0  # 10 second timeout
        )

        # Test simple completion
        start_time = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一個繁體中文助手。"},
                {"role": "user", "content": "請用一句話回答：什麼是洗錢防制？"}
            ],
            temperature=0.0,
            max_tokens=100
        )
        execution_time = time.time() - start_time

        # Extract response
        answer = response.choices[0].message.content
        tokens = response.usage.total_tokens

        print(f"✅ Connection successful!")
        print(f"Execution time: {execution_time:.2f}s")
        print(f"Tokens used: {tokens}")
        print(f"Response: {answer[:200]}...")
        print("=" * 80)

        return True, execution_time, tokens

    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("=" * 80)
        return False, 0.0, 0


def test_langchain_chatopenai_connection():
    """
    Test 2: LangChain ChatOpenAI connection test.

    Purpose: Verify ChatOpenAI integration works with custom LLM gateway.
    """
    print("\n" + "=" * 80)
    print("TEST 2: LangChain ChatOpenAI Connection Test")
    print("=" * 80)

    # Load configuration
    config = ConfigManager()
    settings = config.get_all_settings()

    api_key = settings.get("llm_api_key")
    base_url = settings.get("llm_base_url")
    model = settings.get("llm_model", "gpt-4o-mini")

    print(f"API Key: {api_key[:20]}..." if api_key else "API Key: Not set")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print("-" * 80)

    try:
        # Create ChatOpenAI instance
        llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.0,
            timeout=10.0,  # 10 second timeout
            max_retries=2   # Retry twice on failure
        )

        # Test invocation with messages
        messages = [
            SystemMessage(content="你是一個繁體中文助手。"),
            HumanMessage(content="請用一句話解釋：什麼是金融監管？")
        ]

        start_time = time.time()
        response = llm.invoke(messages)
        execution_time = time.time() - start_time

        # Extract response
        answer = response.content

        print(f"✅ ChatOpenAI connection successful!")
        print(f"Execution time: {execution_time:.2f}s")
        print(f"Response: {answer[:200]}...")
        print("=" * 80)

        return True, execution_time, answer

    except Exception as e:
        print(f"❌ ChatOpenAI connection failed: {str(e)}")
        print("=" * 80)
        return False, 0.0, ""


async def test_langgraph_llm_integration():
    """
    Test 3: LangGraph v1.0 + ChatOpenAI integration test.

    Purpose: Verify LLM works within LangGraph StateGraph workflow.
    Best Practice: StateGraph with TypedDict state, error handling, and observability.
    """
    print("\n" + "=" * 80)
    print("TEST 3: LangGraph v1.0 + ChatOpenAI Integration Test")
    print("=" * 80)

    # Load configuration
    config = ConfigManager()
    settings = config.get_all_settings()

    api_key = settings.get("llm_api_key")
    base_url = settings.get("llm_base_url")
    model = settings.get("llm_model", "gpt-4o-mini")

    print(f"API Key: {api_key[:20]}..." if api_key else "API Key: Not set")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print("-" * 80)

    try:
        # Create ChatOpenAI instance
        llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.0,
            timeout=10.0,
            max_retries=2
        )

        # Define agent node
        def agent_node(state: TestState) -> TestState:
            """Agent node that calls LLM."""
            messages = state.get("messages", [])

            # Add new message
            messages.append(HumanMessage(content="請簡單解釋：什麼是裁罰？"))

            # Call LLM
            start_time = time.time()
            response = llm.invoke(messages)
            execution_time = time.time() - start_time

            # Update state
            messages.append(response)

            return {
                "messages": messages,
                "test_result": response.content,
                "execution_time": execution_time
            }

        # Build StateGraph
        workflow = StateGraph(TestState)
        workflow.add_node("agent", agent_node)
        workflow.add_edge(START, "agent")
        workflow.add_edge("agent", END)

        graph = workflow.compile()

        # Execute graph
        print("Executing LangGraph workflow...")
        initial_state = {
            "messages": [SystemMessage(content="你是一個繁體中文法律助手。")],
            "test_result": "",
            "execution_time": 0.0
        }

        result = await graph.ainvoke(initial_state)

        # Extract results
        answer = result.get("test_result", "")
        execution_time = result.get("execution_time", 0.0)

        print(f"✅ LangGraph integration successful!")
        print(f"Execution time: {execution_time:.2f}s")
        print(f"Response: {answer[:200]}...")
        print("=" * 80)

        return True, execution_time, answer

    except Exception as e:
        print(f"❌ LangGraph integration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 80)
        return False, 0.0, ""


async def test_concurrent_llm_calls():
    """
    Test 4: Concurrent LLM calls stress test.

    Purpose: Verify LLM gateway can handle concurrent requests.
    This simulates the Playwright E2E test scenario where 5 tests run in parallel.
    """
    print("\n" + "=" * 80)
    print("TEST 4: Concurrent LLM Calls Stress Test (5 parallel)")
    print("=" * 80)
    print("Purpose: Simulate Playwright E2E test concurrent load")
    print("-" * 80)

    # Load configuration
    config = ConfigManager()
    settings = config.get_all_settings()

    api_key = settings.get("llm_api_key")
    base_url = settings.get("llm_base_url")
    model = settings.get("llm_model", "gpt-4o-mini")

    print(f"API Key: {api_key[:20]}..." if api_key else "API Key: Not set")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print("-" * 80)

    # Create ChatOpenAI instance
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.0,
        timeout=15.0,  # 15 second timeout for stress test
        max_retries=1
    )

    # Define test queries
    test_queries = [
        "什麼是洗錢防制？",
        "什麼是內線交易？",
        "什麼是金融監管？",
        "什麼是裁罰？",
        "什麼是合規？"
    ]

    async def call_llm(query: str, index: int):
        """Call LLM for a single query."""
        try:
            messages = [
                SystemMessage(content="你是一個繁體中文助手。"),
                HumanMessage(content=f"請用一句話回答：{query}")
            ]

            start_time = time.time()
            response = await llm.ainvoke(messages)
            execution_time = time.time() - start_time

            print(f"  Query {index + 1}: ✅ Success ({execution_time:.2f}s)")
            return True, execution_time

        except Exception as e:
            print(f"  Query {index + 1}: ❌ Failed - {str(e)}")
            return False, 0.0

    # Execute concurrent calls
    print("Executing 5 concurrent LLM calls...")
    start_time = time.time()

    tasks = [call_llm(query, i) for i, query in enumerate(test_queries)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    total_time = time.time() - start_time

    # Analyze results
    successful = sum(1 for r in results if isinstance(r, tuple) and r[0])
    failed = len(results) - successful

    print("-" * 80)
    print(f"Total execution time: {total_time:.2f}s")
    print(f"Successful calls: {successful}/5")
    print(f"Failed calls: {failed}/5")

    if successful >= 3:
        print("✅ Stress test PASSED (≥60% success rate)")
    else:
        print("❌ Stress test FAILED (<60% success rate)")

    print("=" * 80)

    return successful, failed, total_time


async def main():
    """Run all LLM connection tests."""
    print("\n" + "=" * 80)
    print("LLM CONNECTION TEST SUITE")
    print("=" * 80)
    print("Purpose: Verify LLM gateway stability and LangGraph v1.0 integration")
    print("=" * 80)

    results = {}

    # Test 1: Vanilla OpenAI
    success1, time1, tokens1 = test_vanilla_openai_connection()
    results["vanilla_openai"] = success1

    # Test 2: LangChain ChatOpenAI
    success2, time2, answer2 = test_langchain_chatopenai_connection()
    results["chatopenai"] = success2

    # Test 3: LangGraph integration
    success3, time3, answer3 = await test_langgraph_llm_integration()
    results["langgraph"] = success3

    # Test 4: Concurrent stress test
    successful4, failed4, time4 = await test_concurrent_llm_calls()
    results["concurrent"] = (successful4 >= 3)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:30s} {status}")

    print("=" * 80)

    # Overall result
    all_passed = all(results.values())

    if all_passed:
        print("🎉 ALL TESTS PASSED")
        print("\nConclusion:")
        print("- LLM gateway is responsive for single requests")
        print("- ChatOpenAI integration works correctly")
        print("- LangGraph v1.0 StateGraph integration successful")
        print("- Concurrent request handling verified")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\nAnalysis:")
        if not results["vanilla_openai"]:
            print("- Vanilla OpenAI connection failed - check API key and base_url")
        if not results["chatopenai"]:
            print("- ChatOpenAI failed - check LangChain configuration")
        if not results["langgraph"]:
            print("- LangGraph integration failed - check StateGraph setup")
        if not results["concurrent"]:
            print("- Concurrent stress test failed - LLM gateway cannot handle concurrent load")
            print("  This explains why Playwright E2E tests timeout!")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
