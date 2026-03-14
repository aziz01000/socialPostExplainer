#!/usr/bin/env python3
"""Test script for the Social Media QA endpoint."""

import httpx
import json
import asyncio

BASE_URL = "http://localhost:8000"

async def test_qa():
    """Test the /social-qa endpoint with different source types."""
    
    test_cases = [
        ("What is the Ralph Wiggum technique?", "all"),
        ("AI coding agents and their applications", "news"),
        ("Community discussions on Ralph Wiggum", "social"),
    ]
    
    async with httpx.AsyncClient() as client:
        print("🚀 Testing Social Media QA Agent\n")
        print("=" * 70 + "\n")
        
        for question, sources_type in test_cases:
            print(f"❓ Question: {question}")
            print(f"📡 Source Type: {sources_type}\n")
            
            try:
                response = await client.post(
                    f"{BASE_URL}/social-qa",
                    json={"question": question, "sources_type": sources_type, "debug": True},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    print(f"✓ Status: Success")
                    print(f"⏱️  Processing time: {data['processing_time_ms']:.0f}ms\n")
                    
                    print(f"📊 Source Breakdown:")
                    breakdown = data['source_breakdown']
                    print(f"   - FAISS Documents: {breakdown.get('faiss_docs', 0)}")
                    print(f"   - External Total: {breakdown.get('external_total', 0)}")
                    external_by_type = breakdown.get('external_breakdown', {})
                    for source_type_key, count in external_by_type.items():
                        print(f"     • {source_type_key}: {count}")
                    print(f"   - Combined Total: {breakdown.get('combined_total', 0)}\n")
                    
                    print(f"📡 Platforms Represented:")
                    platforms = breakdown.get('platforms', {})
                    for platform, count in platforms.items():
                        print(f"   - {platform}: {count}")
                    print()
                    
                    print(f"💬 Answer Summary ({len(data['answer']['summary'])} chars):\n")
                    summary = data['answer']['summary']
                    display_summary = summary[:400] + "...\n" if len(summary) > 400 else summary + "\n"
                    print(display_summary)
                    
                    print(f"📚 Top 3 Sources:")
                    for i, source in enumerate(data['sources'][:3], 1):
                        platform = (source.get('platform') or 'docs').upper()
                        print(f"   {i}. [{platform}] {source['title'][:60]}...")
                        print(f"      Relevance: {source['relevance_score']:.2f}")
                        if source.get('engagement_score'):
                            print(f"      Engagement: {source['engagement_score']}")

                    if data.get("tool_trace"):
                        print("\n🧰 Tool Trace (preview):")
                        for ev in data["tool_trace"][:6]:
                            tool = ev.get("tool")
                            ms = ev.get("ms")
                            err = ev.get("error")
                            print(f"   - {tool} ({ms}ms)" if ms is not None else f"   - {tool}")
                            if err:
                                print(f"     error: {err}")
                    
                else:
                    print(f"✗ Error: {response.status_code}")
                    print(f"   {response.text}\n")
                    
            except Exception as e:
                print(f"✗ Exception: {e}\n")
            
            print("=" * 70 + "\n")


async def test_explain():
    """Test the /explain endpoint."""
    
    posts = [
        "Just discovered the Ralph Wiggum technique - my code loops are way simpler now!",
        "Geoffrey Huntley's Ralph Wiggum technique hit different in 2025",
    ]
    
    async with httpx.AsyncClient() as client:
        print("\n🚀 Testing Post Explainer Agent\n")
        print("=" * 70 + "\n")
        
        for post in posts:
            print(f"📝 Post: {post}\n")
            
            try:
                response = await client.post(
                    f"{BASE_URL}/explain",
                    json={"post_content": post, "debug": True},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    print(f"✓ Status: Success")
                    print(f"⏱️  Processing time: {data['processing_time_ms']:.0f}ms\n")
                    
                    print(f"📋 Explanation Bullets:")
                    for i, bullet in enumerate(data['explanation'], 1):
                        print(f"   {i}. {bullet[:80]}...")
                    
                    print(f"\n📚 {len(data['sources'])} Source(s):")
                    for source in data['sources'][:2]:
                        print(f"   - {source['title']}")

                    if data.get("tool_trace"):
                        print("\n🧰 Tool Trace (preview):")
                        for ev in data["tool_trace"][:6]:
                            tool = ev.get("tool")
                            ms = ev.get("ms")
                            err = ev.get("error")
                            print(f"   - {tool} ({ms}ms)" if ms is not None else f"   - {tool}")
                            if err:
                                print(f"     error: {err}")
                    
                else:
                    print(f"✗ Error: {response.status_code}")
                    print(f"   {response.text}\n")
                    
            except Exception as e:
                print(f"✗ Exception: {e}\n")
            
            print("=" * 70 + "\n")


async def main():
    """Run all tests."""
    await test_qa()
    await test_explain()


if __name__ == "__main__":
    print("\n🔧 Social Media QA + Post Explainer Test Suite\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✋ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
