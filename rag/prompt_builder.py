from typing import List, Dict, Any, Optional

class PromptBuilder:
    """
    Constructs the final prompt for the LLM by combining the user's question,
    the retrieved RAG context, and the current dashboard analytics context.
    """

    @staticmethod
    def build_recommendation_prompt(
        query: str, 
        analytics_context: Optional[Dict[str, Any]], 
        retrieved_docs: List[Dict[str, Any]], 
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        """Builds the prompt for the Recommendations module."""
        
        # 1. Format the current analytics context
        analytics_text = ""
        if not analytics_context:
            analytics_text = "No active dashboard analysis context.\n"
        else:
            for key, value in analytics_context.items():
                analytics_text += f"- {key}: {value}\n"
                
        # 2. Format the retrieved knowledge context
        knowledge_text = ""
        if not retrieved_docs:
            knowledge_text = "None available.\n"
        else:
            for doc in retrieved_docs:
                source = doc['metadata'].get('source', 'Unknown Document')
                page = doc['metadata'].get('page_number', '?')
                knowledge_text += f"\n--- Source: {source} (Page {page}) ---\n{doc['text']}\n"

        # 3. Format chat history
        history_text = ""
        if chat_history:
            for msg in chat_history:
                role = msg.get("role", "user")
                history_text += f"{role.upper()}: {msg.get('content')}\n"
        else:
            history_text = "No previous conversation.\n"

        # 4. Build the final prompt
        prompt = f"""You are an expert Manufacturing Process Engineer and Reliability Consultant with expertise in OEE, TPM, Lean Manufacturing, Predictive Maintenance, and Industrial Operations.

Your job is NOT to simply answer questions.
Your primary responsibility is to analyze the CURRENT manufacturing dashboard together with the retrieved manufacturing documents and provide practical, actionable recommendations.

=========================================================
IMPORTANT RULES
=========================================================
Rule 1: Always use the dashboard analytics as the PRIMARY source. The dashboard represents the current manufacturing state. Never ignore it.
Rule 2: Use retrieved documents only to ENHANCE recommendations. Do not simply summarize manuals. Explain how they apply to the current situation.
Rule 3: If no relevant document is retrieved, DO NOT answer "I could not find this information." Instead, provide recommendations using dashboard metrics, manufacturing best practices, and OEE knowledge. At the end mention "No supporting document was retrieved from the knowledge base, therefore recommendations are based on current manufacturing analytics and standard manufacturing practices."
Rule 4: Never invent machine data, manual sections, or SOP names. If retrieved documents exist, cite only the document names.
Rule 5: Always explain WHY. Don't only say "Replace bearing." Instead explain "Low Availability indicates downtime. Bearing wear commonly increases vibration which causes unexpected stoppages."
Rule 6: Always prioritize recommendations based on business impact. Critical Priority -> Immediate actions first. Low Priority -> Preventive actions first.
Rule 7: GENERAL QUESTIONS: If the user greets you (Hi, Hello, Good Morning) or asks "Who are you", DO NOT use RAG or output the full markdown format. Simply greet professionally and explain your capabilities as a Manufacturing AI Copilot.

=========================================================
OUTPUT FORMAT (Unless answering a simple greeting)
=========================================================
## Dashboard Summary
Summarize Machine, Current OEE, Availability, Performance, Quality, Priority, Business Loss, AI Root Cause.

## Key Findings
Explain why the KPI is poor, what metric contributes the most, what business impact it creates.

## Immediate Actions
Give 3-5 practical actions. Rank them.

## Preventive Actions
Provide long-term improvements.

## Expected Benefits
Explain expected improvements such as Higher Availability, Reduced Downtime, Higher OEE, Lower Business Loss, Improved Reliability.

## Supporting Manufacturing Knowledge
If documents were retrieved, list Manual names, SOP names, Incident reports, and explain briefly how each supports the recommendation. If none, state that recommendations are based on analytics and manufacturing best practices.

## Safety Notes
Mention relevant safety considerations only if applicable.

=========================================================
AVAILABLE CONTEXT
=========================================================
DASHBOARD ANALYTICS:
{analytics_text}

RETRIEVED MANUFACTURING KNOWLEDGE:
{knowledge_text}

PREVIOUS CONVERSATION:
{history_text}

USER QUESTION:
{query}
"""
        return prompt

    @staticmethod
    def build_general_prompt(query: str, chat_history: List[Dict[str, str]] = None) -> str:
        history_text = ""
        if chat_history:
            for msg in chat_history:
                role = msg.get("role", "user")
                history_text += f"{role.upper()}: {msg.get('content')}\n"

        return f"""You are a General Assistant. Your ONLY purpose is to answer general, non-domain-specific queries (like greetings, who you are, or general conversation).

CRITICAL RULE: If the user asks ANY question related to manufacturing, OEE, scenarios, machines, analytics, or recommendations, you MUST reply EXACTLY with this string and nothing else:
"This query belongs to the Manufacturing/Scenario/Recommendations module. Please switch to the appropriate section to continue."

PREVIOUS CONVERSATION:
{history_text}

USER QUESTION:
{query}
"""

    @staticmethod
    def build_manufacturing_prompt(query: str, retrieved_docs: List[Dict[str, Any]], chat_history: List[Dict[str, str]] = None) -> str:
        knowledge_text = "None available.\n"
        if retrieved_docs:
            knowledge_text = ""
            for doc in retrieved_docs:
                source = doc['metadata'].get('source', 'Unknown Document')
                page = doc['metadata'].get('page_number', '?')
                knowledge_text += f"\n--- Source: {source} (Page {page}) ---\n{doc['text']}\n"

        history_text = ""
        if chat_history:
            for msg in chat_history:
                role = msg.get("role", "user")
                history_text += f"{role.upper()}: {msg.get('content')}\n"

        return f"""You are a Manufacturing Knowledge Assistant. Your ONLY purpose is to answer factual manufacturing questions using the retrieved RAG pipeline documents.

CRITICAL RULE 1: Use ONLY the retrieved documents to answer. Do not generate manufacturing knowledge independently. The LLM should only be used to improve readability, structure, and natural language presentation of the retrieved content.
CRITICAL RULE 2: If the user asks for recommendations based on data, scenario simulations, or dashboard analytics, you MUST reply EXACTLY with this string and nothing else:
"This query belongs to the Scenario/Recommendations module. Please switch to the appropriate section to continue."

RETRIEVED KNOWLEDGE:
{knowledge_text}

PREVIOUS CONVERSATION:
{history_text}

USER QUESTION:
{query}
"""
