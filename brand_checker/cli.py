"""Click CLI for brand consistency checking."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .brand_schema import BrandSpec
from .checker import BrandChecker, CheckResult, Severity

console = Console()

DEFAULT_TEMPLATE = {
    "brand_name": "My Brand",
    "colors": [
        {"name": "Primary Blue", "hex": "#0066CC", "pantone": "PMS 2935 C"},
        {"name": "Dark Gray", "hex": "#333333"},
        {"name": "White", "hex": "#FFFFFF"},
    ],
    "typography": [
        {
            "font_family": "Inter",
            "allowed_sizes": [12, 14, 16, 20, 24, 32, 48],
            "allowed_weights": [400, 600, 700],
        }
    ],
    "logo": {
        "min_width_px": 120,
        "min_height_px": 40,
        "clear_space_ratio": 0.5,
    },
    "voice": {
        "tone_keywords": ["professional", "friendly", "clear"],
        "banned_words": ["cheap", "guaranteed", "revolutionary"],
        "max_sentence_length": 25,
    },
}


def _load_spec(path: str) -> BrandSpec:
    p = Path(path)
    if not p.exists():
        console.print(f"[red]Brand spec not found: {path}[/red]")
        sys.exit(1)
    text = p.read_text(encoding="utf-8")
    if p.suffix in (".yaml", ".yml"):
        data = yaml.safe_load(text)
    elif p.suffix == ".json":
        data = json.loads(text)
    else:
        console.print("[red]Unsupported format. Use .yaml, .yml, or .json[/red]")
        sys.exit(1)
    return BrandSpec(**data)


def _print_result(label: str, result: CheckResult) -> None:
    if result.passed:
        status = Text("PASS", style="bold green")
    else:
        status = Text("FAIL", style="bold red")

    table = Table(title=f"{label} — {status}", show_header=True, header_style="bold")
    table.add_column("Severity", width=8)
    table.add_column("Rule", style="cyan")
    table.add_column("Message")

    for v in result.violations:
        sev_style = {"error": "bold red", "warning": "bold yellow", "info": "blue"}[
            v.severity.value
        ]
        table.add_row(
            Text(v.severity.value.upper(), style=sev_style),
            v.rule,
            v.message,
        )

    if not result.violations:
        table.add_row(Text("—", style="green"), "—", "No violations found")

    console.print(table)
    console.print(f"  Score: {result.score}% ({result.passed_items}/{result.checked_items} passed)\n")


@click.group()
@click.version_option(package_name="brand-consistency-checker")
def cli() -> None:
    """Brand Consistency Checker — eslint for brand design."""


@cli.command()
@click.option("-o", "--output", default="brand.yaml", help="Output file path")
def init(output: str) -> None:
    """Create a brand.yaml template for editing."""
    if os.path.exists(output):
        if not click.confirm(f"{output} already exists. Overwrite?"):
            return

    with open(output, "w", encoding="utf-8") as f:
        yaml.dump(DEFAULT_TEMPLATE, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]Brand template written to {output}[/green]")
    console.print("Edit it to match your brand guidelines, then run:")
    console.print(f"  brand-check check-image --spec {output} --image logo.png")


@cli.command("check-image")
@click.option("--spec", required=True, help="Path to brand spec (YAML/JSON)")
@click.option("--image", required=True, help="Path to image file")
def check_image(spec: str, image: str) -> None:
    """Validate an image against brand color palette and logo rules."""
    brand = _load_spec(spec)
    checker = BrandChecker(brand)
    result = checker.check_image(image)
    _print_result(f"Image: {image}", result)
    sys.exit(0 if result.passed else 1)


@cli.command("check-text")
@click.option("--spec", required=True, help="Path to brand spec (YAML/JSON)")
@click.option("--text", default=None, help="Text string to check")
@click.option("--file", "text_file", default=None, help="File containing text to check")
def check_text(spec: str, text: str | None, text_file: str | None) -> None:
    """Validate text against brand voice and tone guidelines."""
    if text is None and text_file is None:
        console.print("[red]Provide --text or --file[/red]")
        sys.exit(1)

    if text_file:
        p = Path(text_file)
        if not p.exists():
            console.print(f"[red]File not found: {text_file}[/red]")
            sys.exit(1)
        text = p.read_text(encoding="utf-8")

    brand = _load_spec(spec)
    checker = BrandChecker(brand)
    result = checker.check_text(text or "")
    _print_result("Text Check", result)
    sys.exit(0 if result.passed else 1)


@cli.command()
@click.option("--spec", required=True, help="Path to brand spec (YAML/JSON)")
@click.option("--image", default=None, help="Path to image file")
@click.option("--text", default=None, help="Text to check")
@click.option("--text-file", default=None, help="File containing text")
@click.option("-o", "--output", default=None, help="Save report to file")
def report(
    spec: str,
    image: str | None,
    text: str | None,
    text_file: str | None,
    output: str | None,
) -> None:
    """Generate a full brand compliance report."""
    brand = _load_spec(spec)
    checker = BrandChecker(brand)
    checks: list[tuple[str, CheckResult]] = []

    if image:
        checks.append(("Image Check", checker.check_image(image)))

    if text_file:
        p = Path(text_file)
        if p.exists():
            checks.append(("Text Check", checker.check_text(p.read_text(encoding="utf-8"))))

    if text:
        checks.append(("Text Check", checker.check_text(text)))

    if not checks:
        console.print("[yellow]Nothing to check. Provide --image, --text, or --text-file.[/yellow]")
        sys.exit(0)

    report_text = checker.generate_report(checks)
    if output:
        Path(output).write_text(report_text, encoding="utf-8")
        console.print(f"[green]Report saved to {output}[/green]")
    else:
        console.print(Panel(report_text, title="Brand Compliance Report", expand=False))

    all_passed = all(r.passed for _, r in checks)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    cli()
