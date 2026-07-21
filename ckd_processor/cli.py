"""
CLI Interface for Canonical Knowledge Document (CKD) Processor.
"""

import argparse
import sys
import os
import json
from rich.console import Console
from rich.table import Table

from ckd_processor import __version__
from ckd_processor.config import PipelineConfig
from ckd_processor.pipeline import CKDPipeline, ManifestManager

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Canonical Knowledge Document (CKD) Enterprise Preprocessor"
    )
    parser.add_argument("--version", "-v", action="version", version=f"CKD Processor v{__version__}")
    
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: process
    proc_parser = subparsers.add_parser("process", help="Process input directory or file")
    proc_parser.add_argument("--input", "-i", type=str, help="Path to input directory or file")
    proc_parser.add_argument("--output", "-o", type=str, help="Output knowledge directory")
    proc_parser.add_argument("--config", "-c", type=str, default="config.yaml", help="Path to config YAML file")
    proc_parser.add_argument("--provider", type=str, choices=["ollama", "openai", "mock"], help="Override LLM provider")
    proc_parser.add_argument("--model", type=str, help="Override LLM model name")
    proc_parser.add_argument("--workers", type=int, help="Number of parallel worker threads")

    # Command: init
    init_parser = subparsers.add_parser("init", help="Initialize default config.yaml and folder structure")
    init_parser.add_argument("--output-config", type=str, default="config.yaml", help="Config YAML destination")

    # Command: status
    stat_parser = subparsers.add_parser("status", help="Display manifest status & knowledge base stats")
    stat_parser.add_argument("--manifest", type=str, default="./knowledge/manifest.json", help="Path to manifest.json")

    args = parser.parse_args()

    if args.command == "init":
        cfg = PipelineConfig()
        cfg.save_to_yaml(args.output_config)
        os.makedirs("input_docs", exist_ok=True)
        console.print(f"[bold green]Initialized defaults in {args.output_config} and created ./input_docs directory.[/bold green]")
        return

    if args.command == "status":
        manifest_path = args.manifest
        if not os.path.exists(manifest_path):
            console.print(f"[bold red]Manifest file not found at {manifest_path}[/bold red]")
            return

        mm = ManifestManager(manifest_path)
        table = Table(title="CKD Manifest Status Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        total = len(mm.entries)
        success = sum(1 for e in mm.entries.values() if e.status == "success")
        failed = sum(1 for e in mm.entries.values() if e.status == "failed")
        total_chunks = sum(e.chunk_count for e in mm.entries.values() if e.status == "success")

        table.add_row("Total Files Registered", str(total))
        table.add_row("Successfully Converted", str(success))
        table.add_row("Failed Conversions", str(failed))
        table.add_row("Total Chunks Generated", str(total_chunks))

        console.print(table)
        return

    # Default to process
    config_path = getattr(args, "config", "config.yaml")
    config = PipelineConfig.load_from_yaml(config_path)

    if getattr(args, "input", None):
        config.input_dir = args.input
    if getattr(args, "output", None):
        config.output_dir = args.output
    if getattr(args, "provider", None):
        config.llm.provider = args.provider
    if getattr(args, "model", None):
        config.llm.model_name = args.model
    if getattr(args, "workers", None):
        config.parallel_workers = args.workers

    console.print(f"[bold blue]Starting CKD Processing Pipeline...[/bold blue]")
    console.print(f"Input Directory: [yellow]{config.input_dir}[/yellow]")
    console.print(f"Output Knowledge Dir: [yellow]{config.output_dir}[/yellow]")
    console.print(f"LLM Provider: [yellow]{config.llm.provider}[/yellow] (Model: {config.llm.model_name})")

    pipeline = CKDPipeline(config)

    if os.path.isfile(config.input_dir):
        success = pipeline.process_file(config.input_dir)
        if success:
            console.print("[bold green]File processed successfully![/bold green]")
        else:
            console.print("[bold red]File processing failed. Check failed/ logs.[/bold red]")
    else:
        results = pipeline.run_batch()
        console.print(f"[bold green]Batch processing completed. Total: {results['total']}, Success: {results['success']}, Failed: {results['failed']}[/bold green]")


if __name__ == "__main__":
    main()
