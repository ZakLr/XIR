"""Click CLI: parse validate query inspect diff compile test."""
import click
from pathlib import Path
from xir.parser.parse import parse_file
from xir.validator.validate import validate
from xir.query.engine import query, inspect as _inspect, trace_capability, explain as _explain
from xir.diff.diff import diff
from xir.compiler.emit import to_html, to_react, to_a2ui, to_tests, to_docs, to_a11y, to_playwright
from xir.compiler.dsl import to_xir
from xir.patch.patch import apply_patch_text
from xir.semantic.graph import summarize

@click.group()
def main():
    pass

@main.command()
@click.argument("file")
def parse(file):
    exp = parse_file(file)
    click.echo(summarize(exp, 3))

@main.command()
@click.argument("file")
def validate_cmd(file):
    exp = parse_file(file)
    errs = validate(exp)
    click.echo("valid" if not errs else "\n".join(errs))

main.add_command(validate_cmd, "validate")

@main.command()
@click.argument("file")
@click.argument("q")
def query_cmd(file, q):
    click.echo(query(parse_file(file), q))

main.add_command(query_cmd, "query")

@main.command()
@click.argument("file")
@click.argument("kind")
@click.argument("name")
def inspect(file, kind, name):
    exp = parse_file(file)
    if kind == "capability":
        click.echo(trace_capability(exp, name))
    else:
        click.echo(_inspect(exp, kind, name))

@main.command()
@click.argument("file")
@click.argument("kind")
@click.argument("name")
def explain(file, kind, name):
    click.echo(_explain(parse_file(file), kind, name))

@main.command()
@click.argument("file")
@click.argument("patchtext")
def patch(file, patchtext):
    exp = parse_file(file)
    for line in apply_patch_text(exp, patchtext):
        click.echo(line)
    errs = validate(exp)
    click.echo("VALID" if not errs else "INVALID:\n" + "\n".join(errs))

@main.command()
@click.argument("old")
@click.argument("new")
def diff_cmd(old, new):
    click.echo(diff(parse_file(old), parse_file(new)))

main.add_command(diff_cmd, "diff")

@main.command()
@click.argument("file")
@click.option("--target", default="html")
def compile(file, target):
    exp = parse_file(file)
    fn = {"html": to_html, "react": to_react, "a2ui": to_a2ui, "tests": to_tests,
          "docs": to_docs, "a11y": to_a11y, "playwright": to_playwright}[target]
    click.echo(fn(exp))

@main.command()
@click.argument("file")
def test(file):
    exp = parse_file(file)
    errs = validate(exp)
    click.echo(to_tests(exp) + ("\nVALID" if not errs else "\nINVALID:\n" + "\n".join(errs)))

@main.command(name="bench")
def bench():
    from benchmarks.tasks import run_all
    for r in run_all():
        click.echo(f"{r['task']}: ok={r['ok']} {r['seconds']}s chars={r['chars']}")
