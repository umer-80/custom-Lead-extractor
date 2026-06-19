
import json
import os
from typing import Dict, Any
 
class SentinelMemory:
    def __init__(self, history_file="history.json"):
        self.history_file = history_file
        self.memory = self._load_memory()

    def _load_memory(self) -> Dict[str, Any]:
        """Loads the history from the JSON file."""
        if not os.path.exists(self.history_file):
            return {}
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save_memory(self):
        """Saves the current memory to the JSON file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.memory, f, indent=4)

    def remember_lead(self, lead: Dict[str, Any]):
        """Adds a lead to the memory using a unique key (Phone or Website)."""
        key = self._generate_key(lead)
        if key:
            self.memory[key] = {
                "name": lead.get("name"),
                "lead_score": lead.get("lead_score"),
                "timestamp": str(os.path.getmtime(self.history_file) if os.path.exists(self.history_file) else "New")
            }
            self._save_memory()

    def has_seen(self, lead: Dict[str, Any]) -> bool:
        """Checks if the lead exists in memory."""
        key = self._generate_key(lead)
        return key in self.memory

    def _generate_key(self, lead: Dict[str, Any]) -> str:
        """Generates a unique key based on Place ID (highly preferred), Phone, or Website."""
        # v4.0: Use Place ID if available
        place_id = lead.get('place_id')
        if place_id and place_id != "Unknown":
            return place_id

        # Clean phone number (remove spaces, dashes) for better matching
        phone = lead.get('phone', 'N/A')
        if phone and phone != "N/A":
             return "".join(filter(str.isdigit, phone))
        
        # Fallback to website
        website = lead.get('website', 'None')
        if website and website != "None":
            return website

            
        # Fallback to Name (Least reliable but better than nothing)
        return lead.get('name', 'Unknown')
