"""Interactive Command-Line Interface for Aster & Row Support Agent."""
import argparse
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

from src.agent.orchestrator import AgentOrchestrator
from src.agent.observability import AgentTracer


console = Console()


def run_interactive_cli(debug: bool = False):
    """Starts interactive conversation session in terminal."""
    orchestrator = AgentOrchestrator()
    session_id = orchestrator.get_or_create_session()

    console.print(
        Panel.fit(
            "[bold cyan]Aster & Row - AI Customer Support Agent[/bold cyan]\n"
            "[dim]Ecommerce Support for Bags, Drinkware & Travel Gear[/dim]\n\n"
            "Commands:\n"
            "  [yellow]exit[/yellow] / [yellow]quit[/yellow] - Exit chat\n"
            "  [yellow]reset[/yellow]        - Reset conversation session\n"
            "  [yellow]debug[/yellow]        - Toggle trace debug mode",
            border_style="cyan"
        )
    )

    while True:
        try:
            user_input = console.input("\n[bold green]You > [/bold green]").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                console.print("[dim]Goodbye![/dim]")
                break
            elif user_input.lower() == "reset":
                orchestrator.reset_session(session_id)
                console.print("[yellow]Session reset.[/yellow]")
                continue
            elif user_input.lower() == "debug":
                debug = not debug
                console.print(f"[magenta]Debug trace mode set to: {debug}[/magenta]")
                continue

            # Generate Agent Response
            response = orchestrator.chat(user_message=user_input, session_id=session_id)

            # Display Response Panel
            handoff_badge = " [bold red][HANDOFF RECOMMENDED][/bold red]" if response.handoff_recommended else ""
            panel_title = f"[bold cyan]Aster & Row Agent[/bold cyan]{handoff_badge}"

            console.print(
                Panel(
                    Markdown(response.content),
                    title=panel_title,
                    border_style="blue" if not response.handoff_recommended else "red"
                )
            )

            # Display Citations if present
            if response.citations:
                cite_text = " | ".join(c.format_citation() for c in response.citations)
                console.print(f"[dim cyan]Sources: {cite_text}[/dim cyan]")

            # Display Debug Traces if requested
            if debug and response.trace_id:
                trace = orchestrator.tracer.get_trace(response.trace_id)
                if trace:
                    debug_table = Table(title=f"Debug Trace: {trace.trace_id}", show_lines=True)
                    debug_table.add_column("Field", style="bold yellow", width=20)
                    debug_table.add_column("Details", style="dim", width=60)
                    
                    debug_table.add_row("Session ID", trace.session_id)
                    debug_table.add_row("Tool Calls", str(trace.tool_calls))
                    debug_table.add_row("Retrieved Passages", str([f"{p['filename']} ({p['heading']})" for p in trace.retrieved_passages]))
                    debug_table.add_row("Conflicts", str(trace.conflicts_detected))
                    debug_table.add_row("Handoff Decision", str(trace.handoff_recommended))
                    debug_table.add_row("Notes", str(trace.notes))
                    console.print(debug_table)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session terminated.[/dim]")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aster & Row CLI Support Agent")
    parser.add_argument("--debug", action="store_true", help="Enable structured trace logging")
    args = parser.parse_args()

    run_interactive_cli(debug=args.debug)
