"""Script to seed the database with sample EU banking regulations."""
import asyncio
import logging
from datetime import datetime

from src.models import RegulationType
from src.services.document_service import get_ingestion_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample regulatory data for EU banking
SAMPLE_REGULATIONS = [
    {
        "title": "Capital Requirements Regulation (CRR) - Article 92",
        "regulation_type": RegulationType.CRR,
        "content": """
Article 92 - Own funds requirements

1. Institutions shall at all times satisfy the following own funds requirements:
   a) A Common Equity Tier 1 capital ratio of 4.5%
   b) A Tier 1 capital ratio of 6%
   c) A total capital ratio of 8%

2. Institutions shall calculate their Common Equity Tier 1 capital, Tier 1 capital
   and total capital by aggregating their capital requirements for credit risk,
   market risk, operational risk, and additional requirements.

3. The own funds requirements shall be based on risk-weighted exposure amounts
   calculated in accordance with Title II (credit risk), Title IV (market risk),
   and Title III (operational risk).
        """,
        "metadata": {
            "article": "92",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32013R0575"
        }
    },
    {
        "title": "MiFID II - Investment Firm Authorization",
        "regulation_type": RegulationType.MiFID,
        "content": """
MiFID II Article 5 - Authorization of Investment Firms

1. Each Member State shall require that investment services and/or activities
   be provided only by investment firms authorized in accordance with this Directive.

2. Member States shall register all investment firms. The register shall be
   publicly accessible and contain information on the services or activities
   which the investment firm is authorized to provide.

3. Investment firms shall comply with the initial capital requirements and
   organizational requirements set out in Articles 15-20.

4. Authorization shall be granted only where the competent authority is satisfied
   that the firm has adequate capital, governance arrangements, and risk management
   procedures appropriate to the investment services being provided.
        """,
        "metadata": {
            "article": "5",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex:32014L0065"
        }
    },
    {
        "title": "GDPR - Data Processing Requirements",
        "regulation_type": RegulationType.GDPR,
        "content": """
GDPR Article 5 - Principles relating to processing of personal data

1. Personal data shall be:
   a) Processed lawfully, fairly and in a transparent manner
   b) Collected for specified, explicit and legitimate purposes
   c) Adequate, relevant and limited to what is necessary
   d) Accurate and kept up to date
   e) Kept in a form which permits identification for no longer than necessary
   f) Processed in a manner that ensures appropriate security

2. The controller shall be responsible for, and be able to demonstrate compliance
   with, paragraph 1 (accountability).

Banks processing customer data must implement appropriate technical and
organizational measures to ensure compliance with these principles, including
data encryption, access controls, and regular security audits.
        """,
        "metadata": {
            "article": "5",
            "source_url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj"
        }
    },
    {
        "title": "AML Directive - Customer Due Diligence",
        "regulation_type": RegulationType.AML,
        "content": """
Fifth Anti-Money Laundering Directive - Article 13

Customer Due Diligence Requirements:

1. Credit and financial institutions shall apply customer due diligence measures:
   a) When establishing a business relationship
   b) When carrying out occasional transactions exceeding EUR 15,000
   c) When there is suspicion of money laundering or terrorist financing
   d) When there are doubts about previously obtained customer identification data

2. Customer due diligence shall comprise:
   a) Identifying the customer and verifying identity using reliable sources
   b) Identifying the beneficial owner and taking reasonable measures to verify identity
   c) Assessing and obtaining information on the purpose and intended nature
      of the business relationship
   d) Conducting ongoing monitoring of the business relationship

3. Enhanced due diligence shall be applied for high-risk situations, including
   transactions with politically exposed persons (PEPs) and correspondent banking
   relationships with third-country institutions.
        """,
        "metadata": {
            "article": "13",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32018L0843"
        }
    },
    {
        "title": "PSD2 - Strong Customer Authentication",
        "regulation_type": RegulationType.PSD2,
        "content": """
Payment Services Directive 2 - Article 97

Strong Customer Authentication Requirements:

1. Payment service providers shall apply strong customer authentication where
   the payer:
   a) Accesses their payment account online
   b) Initiates an electronic payment transaction
   c) Carries out any action through a remote channel which may imply a risk
      of payment fraud or other abuses

2. Strong customer authentication shall be based on the use of two or more elements
   categorized as:
   a) Knowledge (something only the user knows, e.g., password)
   b) Possession (something only the user possesses, e.g., token)
   c) Inherence (something the user is, e.g., biometric characteristic)

3. The elements shall be mutually independent, such that the breach of one does
   not compromise the reliability of the others.

4. Payment service providers shall have transaction monitoring mechanisms to
   detect unauthorized or fraudulent payment transactions.

Exemptions may apply for low-value transactions under EUR 30 or trusted beneficiaries.
        """,
        "metadata": {
            "article": "97",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32015L2366"
        }
    },
    {
        "title": "BRRD - Recovery and Resolution Planning",
        "regulation_type": RegulationType.BRRD,
        "content": """
Bank Recovery and Resolution Directive - Article 5

Recovery Planning Requirements:

1. Institutions shall draw up and maintain recovery plans providing for measures
   to be taken by the institution to restore its financial position following a
   significant deterioration.

2. Recovery plans shall include:
   a) Options for preserving or restoring financial position and viability
   b) A range of scenarios of severe macroeconomic and financial stress
   c) Appropriate conditions and procedures to ensure timely implementation
   d) Preparatory measures that the institution has taken
   e) Identification of critical functions and core business lines

3. Recovery plans shall be updated at least annually and after any material
   changes to the institution's legal or organizational structure, business,
   or financial position.

4. The recovery plan shall not assume any extraordinary public financial support
   or central bank emergency liquidity assistance.

5. Competent authorities shall assess recovery plans and may require changes
   if deficiencies are identified.
        """,
        "metadata": {
            "article": "5",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014L0059"
        }
    },
    {
        "title": "CRD V - Remuneration Requirements",
        "regulation_type": RegulationType.CRD,
        "content": """
Capital Requirements Directive V - Article 92

Remuneration Policy Requirements:

1. Institutions shall have remuneration policies and practices that are consistent
   with and promote sound and effective risk management.

2. The remuneration policy shall:
   a) Be in line with the business strategy, objectives, values and long-term
      interests of the institution
   b) Include measures to avoid conflicts of interest
   c) Establish appropriate balance between fixed and variable remuneration
   d) Be gender-neutral

3. For identified staff whose professional activities have a material impact on
   risk profile:
   a) At least 50% of variable remuneration shall consist of instruments
      (shares, share-linked instruments, or equivalent)
   b) At least 40% of variable remuneration shall be deferred over a period of
      3-5 years
   c) Variable remuneration shall not exceed 100% of fixed remuneration
      (200% with shareholder approval)

4. Institutions shall establish a Remuneration Committee composed of members of
   the management body who do not perform executive functions.

5. High variable remuneration is subject to malus (adjustment before payment)
   and clawback (recovery after payment) arrangements for at least 7 years.
        """,
        "metadata": {
            "article": "92",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L0878"
        }
    }
]


def seed_database():
    """Seed the database with sample regulations."""
    logger.info("Starting database seeding...")
    
    ingestion_service = get_ingestion_service()
    
    for reg_data in SAMPLE_REGULATIONS:
        logger.info(f"Ingesting: {reg_data['title']}")
        
        response = ingestion_service.ingest_text(
            text=reg_data["content"],
            title=reg_data["title"],
            regulation_type=reg_data["regulation_type"],
            metadata=reg_data.get("metadata", {})
        )
        
        if response.success:
            logger.info(
                f"✓ Successfully ingested: {reg_data['title']} "
                f"({response.chunks_created} chunks)"
            )
        else:
            logger.error(f"✗ Failed to ingest: {reg_data['title']}")
            logger.error(f"  Error: {response.message}")
    
    logger.info("Database seeding completed!")


if __name__ == "__main__":
    seed_database()
