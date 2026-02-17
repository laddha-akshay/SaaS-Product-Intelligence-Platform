#!/usr/bin/env python
"""
Simple demo script to test the SaaS Product Intelligence Platform.
Run with: python demo.py
"""

from app.pipeline import run_pipeline

def main():
    print("\n" + "█" * 80)
    print("█ SaaS Product Intelligence Platform - Demo")
    print("█" * 80)
    
    # Sample queries
    queries = [
        "Why did activation drop in January?",
        "What happened with the onboarding redesign?",
        "Why did support tickets increase?",
    ]
    
    for query in queries:
        print(f"\n📋 QUERY: {query}")
        print("-" * 80)
        
        result = run_pipeline(query)
        
        print(f"\n📊 ANSWER:\n{result['answer']}\n")
        print(f"🔗 CITATIONS:")
        for i, cite in enumerate(result['citations'], 1):
            print(f"   [{i}] {cite}")
        
        print(f"\n📈 METRICS:")
        print(f"   • Confidence: {result['confidence']:.2%}")
        print(f"   • Latency: {result['latency_ms']:.2f}ms")
        print()
    
    print("█" * 80 + "\n")

if __name__ == "__main__":
    main()
