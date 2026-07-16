"""
NIS2 Auditor Agent - Gap Analysis with Gemini AI
Uses Pydantic AI for structured gap identification
"""

from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic import BaseModel, Field
from typing import List
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ComplianceGapOutput(BaseModel):
    """Structured output for a single compliance gap"""
    title: str = Field(description="Short title of the gap")
    category: str = Field(description="Category: TECHNICAL, ORGANIZATIONAL, etc.")
    severity: str = Field(description="CRITICAL, HIGH, MEDIUM, or LOW")
    nis2_article: str = Field(description="NIS2 article reference (e.g., Article 21.2)")
    current_state: str = Field(description="What the client currently has")
    required_state: str = Field(description="What NIS2 requires")
    recommendation: str = Field(description="How to fix this gap")
    risk_score: int = Field(description="Risk score 1-10", ge=1, le=10)
    estimated_effort_hours: int = Field(description="Hours needed to implement")


class GapAnalysisOutput(BaseModel):
    """Complete gap analysis output"""
    gaps: List[ComplianceGapOutput] = Field(description="List of identified compliance gaps")
    overall_compliance_score: float = Field(description="Overall compliance percentage 0-100", ge=0, le=100)
    summary: str = Field(description="Executive summary of findings")
    critical_priorities: List[str] = Field(description="Top 3 critical actions to take")


class NIS2Auditor:
    """
    AI Agent for NIS2 compliance gap analysis
    Uses Gemini via Pydantic AI for structured output
    """
    
    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not configured in settings")
        
        # Initialize Gemini model via Google AI Studio
        provider = GoogleGLAProvider(api_key=settings.GOOGLE_API_KEY)
        model = GeminiModel(
            'gemini-2.0-flash-lite',
            provider=provider
        )
        
        # Create Pydantic AI agent with structured output
        self.agent = Agent(
            model=model,
            output_type=GapAnalysisOutput,
            system_prompt="""You are a NIS2 compliance expert specializing in Dutch IT companies.

Your task is to analyze client security documentation against NIS2 Directive requirements
and identify compliance gaps.

For each gap you identify:
1. Be specific and actionable
2. Reference the exact NIS2 article
3. Explain current state vs required state clearly
4. Provide practical recommendations
5. Assess risk and implementation effort realistically

Categories to check:
- TECHNICAL: Firewalls, encryption, patching
- ORGANIZATIONAL: Policies, procedures, governance
- INCIDENT_RESPONSE: Detection, reporting, recovery
- SUPPLY_CHAIN: Vendor management, contracts
- ACCESS_CONTROL: Authentication, authorization, MFA
- LOGGING: Security logging, retention, monitoring
- TRAINING: Security awareness programs
- GOVERNANCE: Risk management, leadership involvement

Severity levels:
- CRITICAL: Major violation, immediate risk
- HIGH: Significant gap, must fix before certification
- MEDIUM: Should address, notable improvement
- LOW: Nice to have, minor enhancement

Be thorough but realistic. Dutch SMBs need practical, implementable advice."""
        )
    
    async def analyze_compliance(
        self, 
        client_documents: str,
        nis2_requirements: List[str]
    ) -> GapAnalysisOutput:
        """
        Analyze client documents against NIS2 requirements
        
        Args:
            client_documents: Extracted text from client's security documentation
            nis2_requirements: Retrieved NIS2 requirements from RAG (context)
        
        Returns:
            Structured gap analysis with identified issues
        """
        try:
            # Build context for the agent
            context = f"""
CLIENT DOCUMENTATION:
{client_documents[:8000]}  # Limit to avoid token limits

RELEVANT NIS2 REQUIREMENTS:
{chr(10).join(nis2_requirements[:20])}  # Top 20 relevant requirements

Analyze the client's documentation against these NIS2 requirements.
Identify specific gaps, prioritize by risk, and provide actionable recommendations.
"""
            
            # Run agent with structured output
            result = await self.agent.run(context)
            
            logger.info(f"Gap analysis complete: {len(result.output.gaps)} gaps identified")
            return result.output
        
        except Exception as e:
            logger.error(f"Error in compliance analysis: {e}")
            raise
    
    def analyze_compliance_sync(
        self,
        client_documents: str,
        nis2_requirements: List[str]
    ) -> GapAnalysisOutput:
        """
        Synchronous wrapper for analyze_compliance
        """
        import asyncio
        return asyncio.run(self.analyze_compliance(client_documents, nis2_requirements))
