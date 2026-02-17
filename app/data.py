"""Data validation, ingestion, and versioning."""
import json
from datetime import datetime
from typing import Dict, List, Any
import hashlib

class DataValidator:
    """Validates and versions data sources."""
    
    def __init__(self):
        self.version = datetime.utcnow().isoformat()
        self.checksums = {}
    
    def validate_structured_data(self, data: List[Dict[str, Any]]) -> bool:
        """Validate structured data schema."""
        required_keys = {"date", "metric", "value"}
        for row in data:
            if not required_keys.issubset(set(row.keys())):
                return False
        return True
    
    def validate_documents(self, docs: List[str]) -> bool:
        """Validate unstructured documents."""
        return all(isinstance(d, str) and len(d.strip()) > 0 for d in docs)
    
    def detect_drift(self, old_docs: List[str], new_docs: List[str]) -> Dict[str, Any]:
        """Detect data drift by comparing doc distributions."""
        old_hash = hashlib.md5("\n".join(sorted(old_docs)).encode()).hexdigest()
        new_hash = hashlib.md5("\n".join(sorted(new_docs)).encode()).hexdigest()
        return {
            "drifted": old_hash != new_hash,
            "old_hash": old_hash,
            "new_hash": new_hash,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def version_data(self) -> str:
        """Return versioned data identifier."""
        return f"v{self.version}"

class DataLoader:
    """Loads and caches data from sources."""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = base_path
        self.cache = {}
        self.validator = DataValidator()
    
    def load_documents(self, path: str) -> List[str]:
        """Load unstructured documents from file."""
        if path in self.cache:
            return self.cache[path]
        
        try:
            with open(path, 'r') as f:
                content = f.read().strip()
            docs = [line.strip() for line in content.split('\n') if line.strip()]
            if self.validator.validate_documents(docs):
                self.cache[path] = docs
                return docs
        except Exception as e:
            print(f"Error loading {path}: {e}")
        
        return []
    
    def load_structured_csv(self, path: str) -> List[Dict[str, Any]]:
        """Load structured data from CSV."""
        if path in self.cache:
            return self.cache[path]
        
        try:
            import csv
            data = []
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                data = list(reader)
            
            if self.validator.validate_structured_data(data):
                self.cache[path] = data
                return data
        except Exception as e:
            print(f"Error loading {path}: {e}")
        
        return []

