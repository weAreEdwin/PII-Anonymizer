import re
from typing import List, Dict, Set, Tuple
import spacy
from collections import defaultdict


class PIIDetector:
    """Service for detecting PII in text using spaCy NER and regex patterns"""
    
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise RuntimeError(
                "spaCy model 'en_core_web_sm' not found. "
                "Please install it using: python -m spacy download en_core_web_sm"
            )
        
        # Regex patterns for various PII types
        self.patterns = {
            'EMAIL': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'PHONE': re.compile(r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'),
            'SSN': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'CREDIT_CARD': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            'URL': re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'),
            'IP_ADDRESS': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
            'DATE_OF_BIRTH': re.compile(r'\b(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12][0-9]|3[01])[/-](?:19|20)\d{2}\b'),
        }
        
        # Entity type mappings for spaCy
        self.spacy_entity_types = {'PERSON', 'ORG', 'GPE', 'DATE', 'LOC', 'FAC'}
    
    def detect_pii(self, text: str) -> List[Dict]:
        """
        Detect all PII in text using both spaCy NER and regex patterns
        
        Returns:
            List of detected PII entities with metadata
        """
        entities = []
        seen_positions = set()  # Track positions to avoid overlaps
        
        # 1. Detect using regex patterns
        regex_entities = self._detect_with_regex(text)
        for entity in regex_entities:
            start, end = entity['start'], entity['end']
            seen_positions.add((start, end))
            entities.append(entity)
        
        # 2. Detect using spaCy NER
        spacy_entities = self._detect_with_spacy(text)
        for entity in spacy_entities:
            start, end = entity['start'], entity['end']
            # Check for overlaps
            if not self._has_overlap((start, end), seen_positions):
                seen_positions.add((start, end))
                entities.append(entity)
        
        # Sort entities by position in text
        entities.sort(key=lambda x: x['start'])
        
        return entities
    
    def _detect_with_regex(self, text: str) -> List[Dict]:
        """Detect PII using regex patterns"""
        entities = []
        
        for pii_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                entities.append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'type': pii_type,
                    'detection_method': 'regex',
                    'confidence': 1.0  # Regex matches are certain
                })
        
        return entities
    
    def _detect_with_spacy(self, text: str) -> List[Dict]:
        """Detect PII using spaCy NER"""
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in self.spacy_entity_types:
                entities.append({
                    'text': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'type': ent.label_,
                    'detection_method': 'spacy',
                    'confidence': 0.9  # spaCy confidence (could be improved with model scores)
                })
        
        return entities
    
    def _has_overlap(self, position: Tuple[int, int], seen_positions: Set[Tuple[int, int]]) -> bool:
        """Check if a position overlaps with any seen positions"""
        start, end = position
        for seen_start, seen_end in seen_positions:
            # Check for any overlap
            if not (end <= seen_start or start >= seen_end):
                return True
        return False
    
    def aggregate_entities(self, entities: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group entities by type and deduplicate
        
        Returns:
            Dictionary mapping entity types to lists of unique entities
        """
        aggregated = defaultdict(list)
        seen_texts_by_type = defaultdict(set)
        
        for entity in entities:
            entity_type = entity['type']
            entity_text = entity['text']
            
            # Add only if not seen before for this type
            if entity_text not in seen_texts_by_type[entity_type]:
                seen_texts_by_type[entity_type].add(entity_text)
                aggregated[entity_type].append(entity)
        
        return dict(aggregated)
    
    def get_statistics(self, entities: List[Dict]) -> Dict:
        """Get statistics about detected PII"""
        stats = {
            'total_entities': len(entities),
            'by_type': defaultdict(int),
            'by_method': defaultdict(int),
            'unique_values': len(set(e['text'] for e in entities))
        }
        
        for entity in entities:
            stats['by_type'][entity['type']] += 1
            stats['by_method'][entity['detection_method']] += 1
        
        return dict(stats)
