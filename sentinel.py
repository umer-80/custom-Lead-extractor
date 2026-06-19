import os
import sys
import asyncio

# Fix: Add local site-packages BEFORE importing rich
sys.path.append("/home/umarkhan/.local/lib/python3.12/site-packages")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

from src.main import run_navigator, hunt_location

load_dotenv()
console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    clear_screen()
    banner = """
    ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     
    ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     
    ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     
    ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     
    ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
    ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝ v3.0
    """
    console.print(Panel(banner, style="bold cyan", subtitle="Advanced AI Lead Discovery Agent"))

async def run_sentinel(): 
    show_banner() 
    
    # Check for API Keys
    keys = os.getenv("GEMINI_API_KEY", "")
    key_count = len([k for k in keys.split(",") if k.strip()])
    
    if key_count == 0:
        console.print("[bold red]Error:[/bold red] No GEMINI_API_KEY found in .env. Please set them first.")
        return
    
    console.print(f"[bold green]✔ Engine Online[/bold green] ({key_count} API Keys Loaded)")
    console.print("-" * 60)
    
    # 1. Inputs
    niche = Prompt.ask("[bold yellow]What Niche are you hunting?[/bold yellow]", default="Dentist")
    location = Prompt.ask("[bold yellow]Starting Location (City, State/Country)?[/bold yellow]", default="Austin, TX")
    
    mode = Prompt.ask(
        "[bold yellow]Hunt mode?[/bold yellow]", 
        choices=["Commander (Radius)", "Surgical (Single)"], 
        default="Commander (Radius)"
    )
    
    if mode == "Commander (Radius)":
        radius = Prompt.ask("[bold white]Search Radius (e.g. 50km, 10miles)?[/bold white]", default="50km")
        goal = IntPrompt.ask("[bold white]Leads Goal (How many total winners do you want?)[/bold white]", default=50)
        
        console.print("\n[bold cyan]─── Initiating Autonomous Sweep ───[/bold cyan]")
        await run_navigator(niche, location, radius, goal)
        
    else:
        console.print("\n[bold cyan]─── Initiating Surgical Strike ───[/bold cyan]")
        await hunt_location(niche, location)

    console.print("\n[bold green]MISSION COMPLETE.[/bold green] Your gold mines are waiting in the CSV files.")
    console.print("[dim]Press Enter to return to base...[/dim]")
    input()

if __name__ == "__main__":
    asyncio.run(run_sentinel())
