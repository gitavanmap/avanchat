import numpy as np
from typing import List
import os
from collections import Counter
import re

class SimpleEmbeddings:
    """Embeddings simplu pentru MVP - fără dependencies complexe"""
    
    def __init__(self):
        # Cuvinte cheie fiscale importante pentru România
        self.fiscal_keywords = [
            'taxa', 'impozit', 'impozite', 'cladiri', 'teren', 'auto', 'autovehicule',
            'plata', 'scadenta', 'penalitate', 'reducere', 'exceptie', 'scutire',
            'calcul', 'valoare', 'cadastral', 'evaluare', 'procent', 'rata',
            'primarie', 'primaria', 'bucuresti', 'sector', 'hcl', 'hotarare',
            'consiliu', 'local', 'buget', 'venit', 'cheltuiala', 'termen',
            'document', 'formular', 'cerere', 'aprobare', 'aviz', 'licenta'
        ]
    
    def embed_texts(self, texts: List[str]) -> list:
        """Creează embeddings pentru o listă de texte"""
        embeddings = []
        for text in texts:
            embedding = self._text_to_vector(text)
            embeddings.append(embedding)
        return embeddings
    
    def embed_query(self, query: str) -> list:
        """Creează embedding pentru o întrebare"""
        return self._text_to_vector(query)
    
    def _text_to_vector(self, text: str, vector_size: int = 50) -> list:
        """Convertește text în vector numeric"""
        text_clean = self._clean_text(text)
        words = text_clean.split()
        
        # Inițializează vectorul
        vector = [0.0] * vector_size
        
        # Primul set de features: prezența cuvintelor cheie
        for i, keyword in enumerate(self.fiscal_keywords[:vector_size//2]):
            if keyword in text_clean:
                vector[i] = float(text_clean.count(keyword))
        
        # Al doilea set: features generale
        start_idx = len(self.fiscal_keywords)
        if start_idx < vector_size:
            # Lungimea textului (normalizată)
            if start_idx < vector_size:
                vector[start_idx] = min(len(words) / 100.0, 1.0)
                start_idx += 1
            
            # Numărul cifrelor (pentru sume, procente)
            if start_idx < vector_size:
                digits = len(re.findall(r'\d', text))
                vector[start_idx] = min(digits / 10.0, 1.0)
                start_idx += 1
            
            # Prezența simbolurilor de procent sau monedă
            if start_idx < vector_size:
                vector[start_idx] = 1.0 if any(sym in text for sym in ['%', 'lei', 'ron', 'euro']) else 0.0
                start_idx += 1
        
        # Normalizare simplă
        total = sum(abs(x) for x in vector)
        if total > 0:
            vector = [x / total for x in vector]
            
        return vector
    
    def _clean_text(self, text: str) -> str:
        """Curăță și normalizează textul"""
        # Conversie la lowercase
        text = text.lower()
        
        # Înlocuiește diacriticele românești
        replacements = {
            'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
            'ş': 's', 'ţ': 't'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Păstrează doar litere, cifre și spații
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Înlocuiește spațiile multiple cu unul singur
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

# Singleton instance
embeddings_model = SimpleEmbeddings()
