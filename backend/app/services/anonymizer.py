from typing import Dict, List, Tuple
from collections import defaultdict


class Anonymizer:
    """Service for anonymizing PII with consistent placeholders"""
    
    def __init__(self):
        self.placeholder_counters = defaultdict(int)
        self.mapping = {}  # original_text -> placeholder
        self.reverse_mapping = {}  # placeholder -> original_text
    
    def anonymize_text(self, text: str, entities: List[Dict]) -> Tuple[str, Dict[str, str]]:
        """
        Replace PII entities with consistent placeholders
        
        Args:
            text: Original text
            entities: List of detected PII entities (sorted by start position)
        
        Returns:
            Tuple of (anonymized_text, mapping_dict)
        """
        if not entities:
            return text, {}
        
        # Sort entities by position (descending) to replace from end to start
        # This prevents position shifts during replacement
        sorted_entities = sorted(entities, key=lambda x: x['start'], reverse=True)
        
        anonymized_text = text
        
        for entity in sorted_entities:
            original_text = entity['text']
            entity_type = entity['type']
            start = entity['start']
            end = entity['end']
            
            # Get or create placeholder for this entity
            placeholder = self._get_placeholder(original_text, entity_type)
            
            # Replace in text
            anonymized_text = anonymized_text[:start] + placeholder + anonymized_text[end:]
        
        return anonymized_text, self.mapping.copy()
    
    def _get_placeholder(self, original_text: str, entity_type: str) -> str:
        """
        Get consistent placeholder for an entity
        
        Same original text always gets the same placeholder
        """
        # Check if we've already created a placeholder for this text
        if original_text in self.mapping:
            return self.mapping[original_text]
        
        # Create new placeholder
        self.placeholder_counters[entity_type] += 1
        count = self.placeholder_counters[entity_type]
        
        # Format placeholder based on entity type
        placeholder = self._format_placeholder(entity_type, count)
        
        # Store mapping
        self.mapping[original_text] = placeholder
        self.reverse_mapping[placeholder] = original_text
        
        return placeholder
    
    def _format_placeholder(self, entity_type: str, count: int) -> str:
        """Format placeholder based on entity type"""
        # Use different formats for different types
        if entity_type in ['PERSON', 'ORG', 'GPE', 'LOC', 'FAC']:
            # Use letters for named entities
            if entity_type == 'PERSON':
                return f"[PERSON_{count}]"
            elif entity_type == 'ORG':
                return f"[COMPANY_{chr(64 + count)}]"  # A, B, C, etc.
            else:
                return f"[{entity_type}_{count}]"
        else:
            # Use numbers for structured data
            return f"[{entity_type}_{count}]"
    
    def deanonymize_text(self, anonymized_text: str, mapping: Dict[str, str]) -> str:
        """
        Restore original text from anonymized version
        
        Args:
            anonymized_text: Text with placeholders
            mapping: Dictionary of original_text -> placeholder
        
        Returns:
            Original text with PII restored
        """
        # Create reverse mapping
        reverse_map = {v: k for k, v in mapping.items()}
        
        result = anonymized_text
        
        # Sort placeholders by length (descending) to avoid partial replacements
        sorted_placeholders = sorted(reverse_map.keys(), key=len, reverse=True)
        
        for placeholder in sorted_placeholders:
            original_text = reverse_map[placeholder]
            result = result.replace(placeholder, original_text)
        
        return result
    
    def get_mapping_list(self, mapping: Dict[str, str]) -> List[Dict]:
        """
        Convert mapping dictionary to list format for API response
        
        Returns:
            List of mapping entries with metadata
        """
        mapping_list = []
        
        for original, placeholder in mapping.items():
            # Extract type from placeholder
            pii_type = placeholder.split('[')[1].split('_')[0] if '[' in placeholder else 'UNKNOWN'
            
            mapping_list.append({
                'original': original,
                'placeholder': placeholder,
                'type': pii_type
            })
        
        # Sort by placeholder
        mapping_list.sort(key=lambda x: x['placeholder'])
        
        return mapping_list
    
    def reset(self):
        """Reset all mappings and counters"""
        self.placeholder_counters.clear()
        self.mapping.clear()
        self.reverse_mapping.clear()
