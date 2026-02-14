"""Command-line interface for the EU Banking Regulator LLM system."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models import (
    QueryRequest,
    ComplianceCheckRequest,
    RegulationType
)
from src.services.rag_service import get_rag_service


async def interactive_query():
    """Interactive query mode."""
    print("\n" + "=" * 70)
    print("EU Banking Regulator LLM - Interactive Query Mode")
    print("=" * 70)
    print("\nType 'quit' or 'exit' to stop\n")
    
    rag_service = get_rag_service()
    
    while True:
        try:
            question = input("\nYour question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            if not question:
                continue
            
            print("\nProcessing your query...\n")
            
            request = QueryRequest(
                question=question,
                include_references=True,
                max_results=5
            )
            
            response = await rag_service.answer_query(request)
            
            print("-" * 70)
            print(f"ANSWER (Confidence: {response.confidence:.2%}):")
            print("-" * 70)
            print(response.answer)
            
            if response.sources:
                print("\n" + "-" * 70)
                print("SOURCES:")
                print("-" * 70)
                for i, source in enumerate(response.sources, 1):
                    print(f"\n{i}. {source['title']}")
                    print(f"   Type: {source['regulation_type']}")
                    print(f"   Relevance: {source['relevance_score']:.2%}")
                    if source.get('source_url'):
                        print(f"   URL: {source['source_url']}")
            
            print("\n" + "=" * 70)
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")


async def check_compliance_scenario():
    """Check compliance for a scenario."""
    print("\n" + "=" * 70)
    print("EU Banking Regulator LLM - Compliance Checker")
    print("=" * 70)
    
    print("\nDescribe the business scenario to check for compliance:")
    print("(Press Enter twice when done)\n")
    
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    
    scenario = "\n".join(lines)
    
    if not scenario.strip():
        print("No scenario provided.")
        return
    
    print("\nAnalyzing compliance...\n")
    
    rag_service = get_rag_service()
    
    request = ComplianceCheckRequest(
        scenario=scenario,
        detailed_analysis=True
    )
    
    response = await rag_service.check_compliance(request)
    
    print("-" * 70)
    print(f"COMPLIANCE STATUS: {response.status.value.upper()}")
    print("-" * 70)
    print(f"\n{response.summary}\n")
    
    if response.findings:
        print("-" * 70)
        print("KEY FINDINGS:")
        print("-" * 70)
        for i, finding in enumerate(response.findings, 1):
            print(f"\n{i}. {finding['description']}")
    
    if response.recommendations:
        print("\n" + "-" * 70)
        print("RECOMMENDATIONS:")
        print("-" * 70)
        for i, rec in enumerate(response.recommendations, 1):
            print(f"\n{i}. {rec}")
    
    if response.applicable_regulations:
        print("\n" + "-" * 70)
        print("APPLICABLE REGULATIONS:")
        print("-" * 70)
        for reg in response.applicable_regulations:
            print(f"  - {reg.value}")
    
    print("\n" + "=" * 70)


async def main():
    """Main CLI function."""
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "compliance":
            await check_compliance_scenario()
        elif mode == "query":
            await interactive_query()
        else:
            print(f"Unknown mode: {mode}")
            print("Usage: python cli.py [query|compliance]")
    else:
        # Default to interactive query mode
        await interactive_query()


if __name__ == "__main__":
    asyncio.run(main())
