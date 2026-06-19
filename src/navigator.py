
import os
import google.generativeai as genai
from typing import List
import json
from rich.console import Console

console = Console()  

class SentinelNavigator:
    def __init__(self):
        # Support multiple keys: "KEY1,KEY2,KEY3"
        raw_keys = os.getenv("GEMINI_API_KEY", "")
        self.api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        self.current_key_index = 0
        
        if not self.api_keys:
            raise ValueError("No GEMINI_API_KEY found in .env")
            
        self._configure_model()

    def _configure_model(self):
        """Configures the Gemini model with the current key."""
        key = self.api_keys[self.current_key_index]
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def _rotate_key(self):
        """Swaps to the next available API key."""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        console.print(f"[yellow]🔄 Navigator API Limit. Rotating to Key #{self.current_key_index + 1}...[/yellow]")
        self._configure_model()

    def get_locations(self, center: str, radius: str, exclude_list: List[str] = None) -> List[str]:
        """
        Generates a list of strategic locations (towns/suburbs) within the radius of the center.
        """
        console.print(f"[cyan]🧭 Navigator is plotting course around {center} ({radius})...[/cyan]")
        
        exclude_str = ""
        if exclude_list:
            exclude_str = f"IMPORTANT: DO NOT include any of these locations as I have already checked them: {', '.join(exclude_list)}"

        prompt = f"""
        Act as a Geospatial Intelligence Analyst.
        I am hunting for businesses in an area.
        
        Center Location: {center}
        Radius: {radius}
        
        Task: List the top 5-10 most distinct and significant suburbs, towns, or districts within this radius.
        Focus on areas that would have their own business clusters.
        Do not list the Center location itself again.
        {exclude_str}
        
        Output format: JSON Array of strings strings only.
        Example: ["Town A", "Town B", "Suburb C"]
        """

        
        import time
        retries = len(self.api_keys) * 2
        
        for attempt in range(retries):
            try:
                response = self.model.generate_content(prompt)
                text = response.text
                if "```json" in text:
                    text = text.replace("```json", "").replace("```", "")
                
                locations = json.loads(text)
                if isinstance(locations, list):
                    console.print(f"[green]✔ Course Set: Found {len(locations)} targets.[/green]")
                    return locations
                return []
                
            except Exception as e:
                if "429" in str(e) or "Quota exceeded" in str(e):
                    if len(self.api_keys) > 1:
                        self._rotate_key()
                        time.sleep(2)
                        continue
                    else:
                        console.print(f"[yellow]Navigator Rate Limit 429. Waiting 60s...[/yellow]")
                        time.sleep(60)
                        continue
                else:
                    console.print(f"[red]Navigator Error: {e}[/red]")
                    return []
        
        console.print("[red]Navigator gave up after retries.[/red]")
        return []

