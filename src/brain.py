import google.generativeai as genai
import os
import json

class SentinelBrain: 
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
        print(f"[yellow]🔄 API Limit Hit. Rotating to Key #{self.current_key_index + 1}...[/yellow]")
        self._configure_model()

    def analyze_batch(self, batch_data: list):
        """
        Analyzes a batch of leads (v4.0 Batching Protocol).
        Collects 10 leads and sends them in one single request.
        """
        import time
        import random
        
        # Build the batch prompt
        leads_summary = ""
        for i, lead in enumerate(batch_data):
            leads_summary += f"\n--- LEAD #{i+1} ---\n"
            leads_summary += f"Name: {lead.get('name')}\n"
            leads_summary += f"Rating: {lead.get('rating')}\n"
            leads_summary += f"Reviews: {lead.get('reviews')}\n"
            leads_summary += f"Website: {lead.get('website')}\n"
            leads_summary += f"Audit: {json.dumps(lead.get('tech_stack', {}))}\n"

        prompt = f"""
        Act as the "Sentinel Agent" (v4.0).
        Task: Analyze this BATCH of {len(batch_data)} leads. Identify the "Gold Mines."

        **Ranking Algorithm:**
        - P1 (Ghost King): 4.2+ Rating & 20+ Reviews & No Website.
        - P2 (Broken Pro): Website exists but SSL Insecure, No Socials, Copyright < 2022, or Not Mobile Ready.
        - P3 (Modern): Optimized site. (Mark as Junk).

        **Input Data:**
        {leads_summary}

        **Output Format:** Output a JSON ARRAY of objects. Each object must strictly follow this:
        {{
            "thought_process": "Brief CoT analysis.",
            "lead_score": "X/10",
            "priority_status": "Gold Mine | Broken Pro | Optimized",
            "silent_pain": "Deep 1-sentence money-loss insight.",
            "battle_plan": "Specific AI service to sell.",
            "ninety_six_pure_hook": "Pattern interrupt hook."
        }}
        """

        retries_per_key = 2
        total_retries = len(self.api_keys) * retries_per_key
        
        for attempt in range(total_retries):
            try:
                response = self.model.generate_content(prompt)
                text = response.text.replace("```json", "").replace("```", "").strip()
                # Find start of array [ and end of array ] to handle any prefix/suffix garbage
                start = text.find('[')
                end = text.rfind(']') + 1
                if start != -1 and end != -1:
                    text = text[start:end]
                
                results = json.loads(text)
                if isinstance(results, list):
                    return results
                return [self.get_error_fallback()] * len(batch_data)
                
            except Exception as e:
                # Task 5 Backoff Logic: If all keys return 429
                if "429" in str(e) or "Quota exceeded" in str(e):
                    if (attempt + 1) % len(self.api_keys) == 0:
                        # We've tried every key once in this cycle
                        wait_time = 60 + random.randint(1, 15)
                        print(f"[bold red]!! ALL KEYS EXHAUSTED !![/bold red] Sleeping {wait_time}s (Jittered Backoff)...")
                        time.sleep(wait_time)
                    
                    self._rotate_key()
                    time.sleep(2)
                    continue
                
                print(f"[bold red]Gemini Batch Error:[/bold red] {e}")
                return [self.get_error_fallback()] * len(batch_data)

        return [self.get_limit_fallback()] * len(batch_data)

    def get_error_fallback(self):
        return {
            "thought_process": "Error during analysis.",
            "lead_score": "Error",
            "priority_status": "Optimized",
            "silent_pain": "Analysis failed",
            "battle_plan": "Manual Review",
            "ninety_six_pure_hook": "Manual Needed"
        }

    def get_limit_fallback(self):
        return {
            "thought_process": "API Limit reached.",
            "lead_score": "Limit",
            "priority_status": "Optimized",
            "silent_pain": "Rate limit exhausted after retries.",
            "battle_plan": "Check API keys.",
            "ninety_six_pure_hook": "Manual Needed"
        }

    def analyze_lead(self, lead_data: dict):
        """
        [DEPRECATED in v4.0] use analyze_batch for better performance.
        Keeping for backward compatibility.
        """
        results = self.analyze_batch([lead_data])
        return results[0] if results else self.get_error_fallback()


