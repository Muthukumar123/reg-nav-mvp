"""Example usage of the EU Banking Regulator LLM API."""
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


async def example_queries():
    """Run example queries."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Capital Requirements Query")
    print("=" * 70)
    
    rag_service = get_rag_service()
    
    # Example 1: Capital requirements
    request1 = QueryRequest(
        question="What are the minimum capital requirements for EU banks?",
        regulation_types=[RegulationType.CRR],
        include_references=True,
        max_results=3
    )
    
    response1 = await rag_service.answer_query(request1)
    print(f"\nAnswer (Confidence: {response1.confidence:.2%}):")
    print(response1.answer)
    print(f"\nSources: {len(response1.sources)}")
    
    # Example 2: Data protection
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Data Protection Query")
    print("=" * 70)
    
    request2 = QueryRequest(
        question="What are the data processing principles banks must follow under GDPR?",
        regulation_types=[RegulationType.GDPR],
        include_references=True
    )
    
    response2 = await rag_service.answer_query(request2)
    print(f"\nAnswer (Confidence: {response2.confidence:.2%}):")
    print(response2.answer)
    
    # Example 3: AML requirements
    print("\n" + "=" * 70)
    print("EXAMPLE 3: AML Customer Due Diligence")
    print("=" * 70)
    
    request3 = QueryRequest(
        question="When must banks perform customer due diligence under AML regulations?",
        regulation_types=[RegulationType.AML],
        include_references=True
    )
    
    response3 = await rag_service.answer_query(request3)
    print(f"\nAnswer (Confidence: {response3.confidence:.2%}):")
    print(response3.answer)


async def example_compliance_check():
    """Run example compliance check."""
    print("\n" + "=" * 70)
    print("EXAMPLE: Compliance Check")
    print("=" * 70)
    
    rag_service = get_rag_service()
    
    scenario = """
    Our bank is planning to launch a new mobile banking app that will allow customers
    to make payments up to EUR 50 using just their phone number and a 4-digit PIN.
    We want to make the user experience as smooth as possible, so we're considering
    skipping biometric authentication for these low-value transactions.
    """
    
    request = ComplianceCheckRequest(
        scenario=scenario,
        regulation_types=[RegulationType.PSD2, RegulationType.GDPR],
        detailed_analysis=True
    )
    
    response = await rag_service.check_compliance(request)
    
    print(f"\nCompliance Status: {response.status.value.upper()}")
    print(f"\nSummary:\n{response.summary}")
    
    if response.findings:
        print("\nKey Findings:")
        for i, finding in enumerate(response.findings, 1):
            print(f"{i}. {finding['description']}")
    
    if response.recommendations:
        print("\nRecommendations:")
        for i, rec in enumerate(response.recommendations, 1):
            print(f"{i}. {rec}")


async def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("EU Banking Regulator LLM - Example Usage")
    print("=" * 70)
    
    # Run example queries
    await example_queries()
    
    # Run example compliance check
    await example_compliance_check()
    
    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
