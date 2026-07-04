from typing import Tuple


class DomainIntelligenceEngine:
    """
    Analyzes research topics to dynamically classify academic disciplines
    and determine appropriate non-forced investigation methodologies.
    Zero synthetic or hardcoded fallback generation.
    """
    
    @staticmethod
    def classify_domain_and_methodology(topic: str) -> Tuple[str, str, str]:
        """
        Returns (discipline_name, primary_methodology, methodology_description).
        Prevents forcing computational code simulation on humanities, qualitative, or theoretical fields.
        """
        t_lower = topic.lower()
        
        # 1. Linguistics, Language, Education & Communication
        if any(w in t_lower for w in ["language", "linguist", "learning transfer", "second language", "l2", "education", "pedagog", "speech", "discourse", "emergency context", "maritime communication"]):
            return (
                "Applied Linguistics & Communication Studies",
                "qualitative_case_study",
                "Rigorous qualitative protocol analysis, comparative discourse evaluation, and empirical case study synthesis across multilingual operational environments."
            )
        
        # 2. Social Sciences, Sociology, Psychology & Organizational Behavior
        elif any(w in t_lower for w in ["social", "psycholog", "behav", "organilat", "workforce", "ethic", "governance", "policy", "law", "legal"]):
            return (
                "Social & Behavioral Sciences",
                "systematic_literature_review",
                "Systematic literature review (PRISMA framework), comparative policy meta-analysis, and empirical survey evidence synthesis."
            )
            
        # 3. Medical, Clinical, Epidemiology & Biological Sciences
        elif any(w in t_lower for w in ["medic", "clinic", "cancer", "protein", "dna", "rna", "gene", "diseas", "patient", "drug", "therap", "hospital", "epidemiol"]):
            return (
                "Biomedical & Clinical Sciences",
                "comparative_meta_analysis",
                "Systematic clinical meta-analysis, randomized controlled trial (RCT) evidence evaluation, and statistical risk factor modeling."
            )
            
        # 4. Economics, Finance, Business & Market Dynamics
        elif any(w in t_lower for w in ["econom", "financ", "market", "trad", "gdp", "inflation", "supply chain", "business", "logist"]):
            return (
                "Economics & Business Sciences",
                "statistical_survey_analysis",
                "Econometric regression modeling, statistical time-series evaluation, and comparative industry benchmark analysis."
            )
            
        # 5. Computer Science, AI, Engineering & Math (Where simulation is appropriate)
        elif any(w in t_lower for w in ["algoritm", "comput", "grid", "network", "ai", "machine learning", "neural", "quant", "robot", "optimilat", "latency", "scalab"]):
            return (
                "Computer Science & Systems Engineering",
                "computational_simulation",
                "Automated computational simulation, Monte Carlo numerical modeling, algorithmic asymptotic complexity proofs, and benchmark latency charting."
            )
            
        # Default Multidisciplinary Fallback
        else:
            return (
                "Multidisciplinary Scientific Investigation",
                "systematic_literature_review",
                "Rigorous comparative evidence synthesis, theoretical framework formulation, and systematic cross-disciplinary literature analysis."
            )
