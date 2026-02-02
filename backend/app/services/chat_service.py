"""
Chat Service - Simple Q&A on anonymized documents
"""
from typing import List, Dict, Tuple
import re
from datetime import datetime


class ChatService:
    """Service for chat/Q&A on anonymized documents"""
    
    def __init__(self):
        self.chat_history = {}  # Store chat history per session
    
    def find_context(self, document: str, query: str, context_window: int = 200) -> List[Dict[str, str]]:
        """
        Find relevant context in document based on query keywords
        
        Args:
            document: The anonymized document text
            query: User's question
            context_window: Number of characters around match to include
            
        Returns:
            List of context snippets with their positions
        """
        # Extract keywords from query (simple approach)
        keywords = self._extract_keywords(query)
        
        if not keywords:
            return []
        
        # Find matches in document
        contexts = []
        document_lower = document.lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            start = 0
            
            while True:
                # Find next occurrence
                pos = document_lower.find(keyword_lower, start)
                if pos == -1:
                    break
                
                # Extract context around the match
                context_start = max(0, pos - context_window)
                context_end = min(len(document), pos + len(keyword) + context_window)
                context_text = document[context_start:context_end]
                
                # Add ellipsis if truncated
                if context_start > 0:
                    context_text = "..." + context_text
                if context_end < len(document):
                    context_text = context_text + "..."
                
                contexts.append({
                    "text": context_text,
                    "position": pos,
                    "keyword": keyword
                })
                
                start = pos + len(keyword)
        
        # Sort by position and remove duplicates
        contexts = sorted(contexts, key=lambda x: x['position'])
        
        # Remove overlapping contexts
        filtered_contexts = []
        last_end = -1
        
        for ctx in contexts:
            if ctx['position'] > last_end:
                filtered_contexts.append(ctx)
                last_end = ctx['position'] + context_window
        
        return filtered_contexts[:5]  # Return top 5 contexts
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract meaningful keywords from query
        
        Args:
            query: User's question
            
        Returns:
            List of keywords
        """
        # Remove common stop words
        stop_words = {
            'what', 'where', 'when', 'who', 'why', 'how', 'is', 'are', 'was', 'were',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'about', 'this', 'that', 'these', 'those',
            'can', 'could', 'will', 'would', 'should', 'may', 'might', 'do', 'does',
            'did', 'has', 'have', 'had', 'be', 'been', 'being', 'me', 'you', 'it'
        }
        
        # Tokenize and filter
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Also look for placeholder patterns
        placeholders = re.findall(r'\[[\w_]+\]', query)
        keywords.extend(placeholders)
        
        return keywords
    
    def generate_response(
        self,
        query: str,
        contexts: List[Dict[str, str]],
        session_id: str
    ) -> str:
        """
        Generate a response based on found contexts
        
        Args:
            query: User's question
            contexts: Relevant contexts from document
            session_id: Session identifier
            
        Returns:
            Generated response
        """
        if not contexts:
            return (
                "I couldn't find specific information related to your question in the document. "
                "Try rephrasing your question or using different keywords. You can also refer to "
                "specific placeholders like [PERSON_1] or [COMPANY_A] in your query."
            )
        
        # Build response with contexts
        response_parts = [
            f"Based on the anonymized document, here's what I found related to your question:\n"
        ]
        
        for i, ctx in enumerate(contexts, 1):
            response_parts.append(f"\n**Context {i}:**")
            response_parts.append(ctx['text'])
        
        response_parts.append(
            "\n\nNote: This is a simple keyword-based search. "
            "For more advanced analysis, consider exporting the anonymized document "
            "and using a full AI assistant."
        )
        
        response = "\n".join(response_parts)
        
        # Store in chat history
        self._add_to_history(session_id, query, response)
        
        return response
    
    def _add_to_history(self, session_id: str, user_message: str, bot_response: str):
        """
        Add conversation to chat history
        
        Args:
            session_id: Session identifier
            user_message: User's message
            bot_response: Bot's response
        """
        if session_id not in self.chat_history:
            self.chat_history[session_id] = []
        
        self.chat_history[session_id].append({
            "timestamp": datetime.utcnow().isoformat(),
            "user": user_message,
            "bot": bot_response
        })
        
        # Keep only last 50 messages per session
        if len(self.chat_history[session_id]) > 50:
            self.chat_history[session_id] = self.chat_history[session_id][-50:]
    
    def get_chat_history(self, session_id: str) -> List[Dict]:
        """
        Get chat history for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of chat messages
        """
        return self.chat_history.get(session_id, [])
    
    def clear_chat_history(self, session_id: str):
        """
        Clear chat history for a session
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.chat_history:
            del self.chat_history[session_id]
    
    async def process_query(
        self,
        session_id: str,
        query: str,
        document: str
    ) -> Tuple[str, List[Dict]]:
        """
        Process a chat query and return response with contexts
        
        Args:
            session_id: Session identifier
            query: User's question
            document: The anonymized document text
            
        Returns:
            Tuple of (response, contexts)
        """
        # Find relevant contexts
        contexts = self.find_context(document, query)
        
        # Generate response
        response = self.generate_response(query, contexts, session_id)
        
        return response, contexts
    
    def suggest_questions(self, document: str, pii_types: List[str]) -> List[str]:
        """
        Suggest sample questions based on document content
        
        Args:
            document: The anonymized document text
            pii_types: List of PII types detected
            
        Returns:
            List of suggested questions
        """
        suggestions = []
        
        # Generic suggestions
        suggestions.append("What is this document about?")
        suggestions.append("Summarize the main points")
        
        # PII-specific suggestions
        if "PERSON" in pii_types:
            suggestions.append("Who are the people mentioned?")
            suggestions.append("What is [PERSON_1]'s role?")
        
        if "COMPANY" in pii_types or "ORG" in pii_types:
            suggestions.append("Which organizations are mentioned?")
            suggestions.append("What is [COMPANY_A]'s involvement?")
        
        if "EMAIL" in pii_types:
            suggestions.append("What contact information is available?")
        
        if "DATE" in pii_types:
            suggestions.append("What are the important dates?")
        
        if "ADDRESS" in pii_types or "LOCATION" in pii_types:
            suggestions.append("What locations are mentioned?")
        
        return suggestions[:6]  # Return top 6 suggestions
