import argparse
import asyncio
import os
import sys
 
# Add the src directory to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add local site-packages for dependencies
sys.path.append("/home/umarkhan/.local/lib/python3.12/site-packages")

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
import pandas as pd
from src.scraper import SentinelScraper
from src.brain import SentinelBrain

# Load environment variables
load_dotenv()

console = Console()



# Initialize Memory Once
from src.memory import SentinelMemory
memory = SentinelMemory()

async def hunt_location(niche: str, location: str, navigator_mode=False):
    """
    Runs the hunt for a SINGLE location.
    """
    console.print(f"[bold green]The Sentinel is hunting for:[/bold green] {niche} in {location}")
    
    # Check for API Key
    if not os.getenv("GEMINI_API_KEY"):
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY not found in .env")
        return

    scraper = SentinelScraper()
    brain = SentinelBrain()
    
    console.print(f"[yellow]Phase 1: Deploying 'The Eyes' in {location}...[/yellow]")
    leads = await scraper.search_google_maps(niche, location)
    
    if not leads:
        console.print(f"[bold red]No leads found in {location}. Moving on...[/bold red]")
        return []

    console.print(f"[green]Found {len(leads)} raw leads in {location}.[/green]")
    
    analyzed_leads = [] # Local list for this location
    
    # Create a table for live output
    table = Table(title=f"Results: {location}")
    table.add_column("Business Name", style="cyan")
    table.add_column("Phone", style="white")
    table.add_column("Score", style="magenta")
    table.add_column("Strategy", style="green")
    
    
    # Intelligence Config
    SATURATION_CHECK_LIMIT = 5
    SATURATION_THRESHOLD = 0.6 # If 60% have tech, it's saturated.
    tech_hits = 0
    scout_count = 0
    
    current_batch = []
    
    for i, lead in enumerate(leads):
        # Check Memory (Deduplication)
        if memory.has_seen(lead):
            console.print(f"[dim]🧠 Skipping {lead['name']} (Already in Memory)[/dim]")
            continue

        console.print(f"[{i+1}/{len(leads)}] Scouting: [bold]{lead['name']}[/bold]...")
        
        # Detailed Scouting (SSL, Mobile, Age, Phone)
        if lead['website'] != "None":
            tech_stack = await scraper.visit_website(lead['website'])
            lead['tech_stack'] = tech_stack
        else:
            lead['tech_stack'] = {"site_status": "No Website"}
        
        # Saturation Check
        if i < SATURATION_CHECK_LIMIT:
            scout_count += 1
            has_tech = lead['tech_stack'].get('has_chatbot', False) or lead['tech_stack'].get('has_booking', False)
            if has_tech:
                tech_hits += 1
            
            if scout_count == SATURATION_CHECK_LIMIT:
                saturation_score = tech_hits / scout_count
                if saturation_score >= SATURATION_THRESHOLD:
                    console.print(f"[bold red]🛑 SATURATION ALERT: {location} Score: {saturation_score:.1%}[/bold red]")
                    return analyzed_leads 
                else:
                    console.print(f"[bold green]💎 GOLD MINE DETECTED: {location} Saturation: {saturation_score:.1%}[/bold green]")

        # Push to batch for AI Analysis
        current_batch.append(lead)
        
        # Process batch if it hits 10 OR if it's the last lead
        if len(current_batch) >= 10 or (i == len(leads) - 1 and current_batch):
            console.print(f"[bold cyan]📦 Dispatching Batch of {len(current_batch)} for AI Analysis...[/bold cyan]")
            batch_results = brain.analyze_batch(current_batch)
            
            for lead_data, analysis in zip(current_batch, batch_results):
                # Flatten tech_stack for CSV columns (Socials, SSL, etc.)
                tech = lead_data.pop('tech_stack', {})
                full_lead = {**lead_data, **tech, **analysis, "scouted_location": location}
                analyzed_leads.append(full_lead)

                
                # Remember the lead
                memory.remember_lead(full_lead)
                
                # Add to Table
                table.add_row(
                    full_lead['name'],
                    full_lead.get('phone', 'N/A'),
                    full_lead.get('lead_score', 'N/A'),
                    full_lead.get('battle_plan', 'N/A')
                )
            
            current_batch = [] # Reset for next batch

    console.print(table)
    return analyzed_leads


async def run_navigator(niche: str, center: str, radius: str, goal: int = 50):
    from src.navigator import SentinelNavigator
    nav = SentinelNavigator()
    
    all_leads = []
    scanned_locations = []
    
    # Starting values
    current_radius_str = radius # e.g. "50km"
    try:
        current_radius_val = int("".join(filter(str.isdigit, radius)))
        unit = "".join(filter(str.isalpha, radius))
    except:
        current_radius_val = 50
        unit = "km"

    # Recursive Expansion Loop
    while len(all_leads) < goal:
        locations = nav.get_locations(center, current_radius_str, exclude_list=scanned_locations)
        
        if not scanned_locations:
            locations.insert(0, center) # First run includes center

        if not locations:
            console.print("[yellow]Navigator found no new locations. Expanding search radius...[/yellow]")
            current_radius_val += 10
            current_radius_str = f"{current_radius_val}{unit}"
            if current_radius_val > 200: # Safety break
                console.print("[red]Max expansion (200km) reached. Stopping hunt.[/red]")
                break
            continue

        for loc in locations:
            if len(all_leads) >= goal:
                break
                
            scanned_locations.append(loc)
            console.rule(f"[bold purple]Navigate: Arriving at {loc} ({len(all_leads)}/{goal})[/bold purple]")
            leads = await hunt_location(niche, loc, navigator_mode=True)
            if leads:
                all_leads.extend(leads)
                
            # Save Aggregate immediately (Sentinel v4.0 Layout)
            if all_leads:
                filename = f"leads_v4_{niche}_{center}.csv".replace(" ", "_").replace(",", "")
                df = pd.DataFrame(all_leads)
                
                # Standardize Socials list to string for CSV
                if "social_links" in df.columns:
                    df['social_links'] = df['social_links'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

                # Rename columns to match v4.0 Professional Requirements
                column_mapping = {
                    "name": "1. Business Name",
                    "priority_status": "2. Lead Status",
                    "phone": "3. Phone",
                    "social_links": "4. Socials",
                    "silent_pain": "5. Silent Pain",
                    "battle_plan": "6. Battle Plan",
                    "ninety_six_pure_hook": "7. Hook"
                }
                
                # Keep only specific columns and order them
                existing_cols = [c for c in column_mapping.keys() if c in df.columns]
                final_df = df[existing_cols].rename(columns=column_mapping)
                
                # Sort by score if possible (we need to revert renaming or use original df for sorting)
                if "lead_score" in df.columns:
                    # Sort the original df and then slice/rename
                    df = df.sort_values(by="lead_score", ascending=False)
                    final_df = df[existing_cols].rename(columns=column_mapping)

                final_df.to_csv(filename, index=False)
                console.print(f"[bold green]✔ Sentinel v4.0 Export: {len(all_leads)} leads saved to {filename}[/bold green]")


        # If we finished all locations but goal still not met
        if len(all_leads) < goal:
            console.print(f"[yellow]Finished all locations in {current_radius_str} but only found {len(all_leads)}/{goal} leads. Expanding...[/yellow]")
            current_radius_val += 10
            current_radius_str = f"{current_radius_val}{unit}"
            if current_radius_val > 150: # Slightly lower threshold for town search
                 console.print("[red]Final expansion reached. Stopping.[/red]")
                 break
        else:
            console.print(f"[bold green]🎯 Goal of {goal} leads reached! Mission accomplished.[/bold green]")
            break



def main():
    parser = argparse.ArgumentParser(description="The Sentinel: AI Agency Lead Auditor & Scorer")
    parser.add_argument("niche", type=str, help="The business niche (e.g., 'Dentist')")
    parser.add_argument("location", type=str, help="The location (e.g., 'New York')")
    parser.add_argument("--radius", type=str, help="Radius for Navigator Mode (e.g. '50km')", default=None)
    parser.add_argument("--goal", type=int, help="Target number of leads to find (default: 50)", default=50)
    
    args = parser.parse_args()
    
    try:
        if args.radius:
            asyncio.run(run_navigator(args.niche, args.location, args.radius, args.goal))
        else:
            # Single Mode
            leads = asyncio.run(hunt_location(args.niche, args.location))
            if leads:
                filename = f"leads_{args.niche}_{args.location}.csv".replace(" ", "_")
                df = pd.DataFrame(leads)
                df.to_csv(filename, index=False)
                console.print(f"[bold green]Results saved to {filename}[/bold green]")

    except KeyboardInterrupt:
        console.print("\n[bold red]Hunt User Interrupted. Data saved safely.[/bold red]")

if __name__ == "__main__":
    main()
