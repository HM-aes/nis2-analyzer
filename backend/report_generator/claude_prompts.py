"""
All Claude prompts for NIS2 report generation.
Prompts are structured for use with the Anthropic API.
"""

SECTOR_REPORT_SYSTEM = """
You are an expert NIS2 compliance consultant.
You generate professional compliance reports for
organisations in the EU. Your reports are precise,
actionable, and based on the actual NIS2 Directive
(EU) 2022/2555. Always cite specific articles.
Respond in English unless instructed otherwise.
Format all output as clean prose suitable for
a professional PDF report.
"""

SECTOR_REQUIREMENTS_PROMPT = """
Generate a comprehensive NIS2 compliance requirements
report for the following organisation:

Company: {company_name}
Sector: {sector}
Country: {country}
Entity Classification: {entity_type}
Company Size: {company_size}

Based on NIS2 Directive (EU) 2022/2555, provide:

1. ENTITY CLASSIFICATION
   Confirm whether this organisation is an Essential
   Entity or Important Entity under Article 3.
   Explain the classification criteria that apply.

2. MANDATORY REQUIREMENTS (Article 21)
   List all 10 mandatory cybersecurity risk management
   measures that apply to this sector. For each:
   - Requirement description
   - What evidence regulators expect
   - Typical implementation approach

3. INCIDENT REPORTING OBLIGATIONS (Article 23)
   Explain the 24-hour early warning requirement,
   72-hour notification, and monthly final report.
   Include country-specific reporting authority
   for {country}.

4. GOVERNANCE REQUIREMENTS (Article 20)
   Explain board and executive accountability
   obligations. Include personal liability risks.

5. SUPPLY CHAIN SECURITY (Article 21.2d)
   Requirements specific to {sector} supply chain.

6. COUNTRY-SPECIFIC REQUIREMENTS
   Additional requirements under {country} national
   transposition of NIS2.

7. PENALTIES
   Maximum fines for Essential vs Important entities.
   Personal liability for executives.

8. RECOMMENDED NEXT STEPS
   Prioritised action list for this sector and size.

Write in professional English suitable for a board
presentation. Be specific, not generic.
"""

EXECUTIVE_SUMMARY_PROMPT = """
Write a professional executive summary for a NIS2
gap analysis report for the following organisation:

Company: {company_name}
Sector: {sector}
Compliance Score: {compliance_score}%
Total Gaps: {total_gaps}
Critical Gaps: {critical_gaps}
High Gaps: {high_gaps}
Medium Gaps: {medium_gaps}
Low Gaps: {low_gaps}
Total Remediation Hours: {remediation_hours}
Estimated Remediation Cost: €{remediation_cost}

Key gaps found:
{top_gaps_summary}

Write 3-4 paragraphs covering:
1. Overall compliance posture and score interpretation
2. Most critical findings requiring immediate action
3. Remediation effort and timeline overview
4. Risk to the organisation if gaps not addressed

Tone: Professional, direct, board-level audience.
Do not use bullet points. Prose only.
Maximum 400 words.
"""

REMEDIATION_ROADMAP_PROMPT = """
Create a prioritised remediation roadmap for this
NIS2 gap analysis:

Gaps (JSON):
{gaps_json}

Organisation:
- Sector: {sector}
- Size: {company_size}
- Country: {country}

Create a 3-phase roadmap:
PHASE 1 (0-30 days): Critical and quick wins
PHASE 2 (30-90 days): High severity gaps
PHASE 3 (90-180 days): Medium severity gaps

For each phase list:
- Specific gaps to address
- Recommended approach
- Resource requirements
- Expected outcome

Write as professional prose with clear phase headings.
"""

GAP_NARRATIVE_PROMPT = """
Write a professional finding description for this
NIS2 compliance gap:

Gap Title: {title}
Category: {category}
Severity: {severity}
Current State: {current_state}
Required State: {required_state}
Business Impact: {business_impact}
NIS2 Article: {article_reference}

Write 2-3 sentences explaining:
1. What is currently missing or insufficient
2. What NIS2 requires (cite the article)
3. The business and regulatory risk

Professional tone. No bullet points. 100 words max.
"""

FINE_EXPOSURE_PROMPT = """
Calculate and explain the regulatory fine exposure
for this organisation:

Entity Type: {entity_type}
Annual Turnover: {annual_turnover}
Country: {country}
Critical Gaps: {critical_gaps}
Total Gaps: {total_gaps}

Explain:
1. Maximum fine under NIS2 for their entity type
2. Calculated maximum based on their size
3. Country-specific enforcement context in 2026
4. Personal liability risk for executives
5. Non-financial penalties (public disclosure,
   operating restrictions)

Be specific with euro amounts. Professional tone.
"""
