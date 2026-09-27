"""XIR CLI. Every command runs on the semantic IR, never on the syntax AST."""
import click
from xir.ir import load_file, load, graph_of
from xir.parser.parse import ParseError, recover_text
from xir.validator.validate import validate as check_model
from xir.query import engine as Q
from xir.diff.diff import diff
from xir.compiler import emit as E
from xir.compiler.dsl import to_xir
from xir.patch.patch import apply_text, PatchError
from xir.semantic.levels import summarize


def _model(path):
    return load_file(path)


@click.group()
@click.version_option(package_name="xir", prog_name="xir")
def main():
    """XIR — the semantic IR for interactive products."""


@main.command()
@click.argument("file")
@click.option("--level", default="3", help="context level L0..L6")
def parse(file, level):
    m = _model(file)
    click.echo(summarize(m, int(level)))


@main.command(name="validate")
@click.argument("file")
def validate_cmd(file):
    m = _model(file)
    findings = check_model(m)
    if not findings:
        click.echo(f"valid: {m.name} [{m.id}] {len(m.all_ids())} semantic nodes")
        return
    for f in findings:
        click.echo(str(f))
    raise SystemExit(1)


@main.command()
@click.argument("file")
@click.argument("q")
def query(file, q):
    click.echo(Q.query(graph_of(_model(file)), q))


@main.command()
@click.argument("file")
@click.argument("ref")
def inspect(file, ref):
    """Compact semantic slice for an agent (§16)."""
    click.echo(Q.show(graph_of(_model(file)), ref))


@main.command()
@click.argument("file")
@click.argument("ref")
def trace(file, ref):
    """What happens when this capability fires (§33)."""
    click.echo(Q.trace(graph_of(_model(file)), ref))


@main.command()
@click.argument("file")
@click.argument("ref")
@click.argument("relation")
@click.option("--depth", default=1)
def follow(file, ref, relation, depth):
    click.echo(Q.follow(graph_of(_model(file)), ref, relation, depth))


@main.command()
@click.argument("old")
@click.argument("new")
def diff_cmd(old, new):
    """Semantic diff between two .xir files: renames are distinguished from remove+add."""
    click.echo(diff(_model(old), _model(new)))


@main.command()
@click.argument("file")
@click.option("--target", default="react", type=click.Choice(sorted(E.TARGETS)),
              help="projection to emit")
@click.option("--out", type=click.Path(), help="write to a file instead of stdout")
def compile(file, target, out):
    m = _model(file)
    text = E.emit(m, target)
    if out:
        click.echo(f"wrote {out}", err=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        click.echo(text)


def _fmt_op(op) -> str:
    name, ref, kwargs = op[0], op[1], (op[2] if len(op) > 2 else {})
    args = " ".join(f"{k}={v}" for k, v in kwargs.items() if v not in (None, "", []))
    return f"{name} {ref}" + (f"  [{args}]" if args else "")


@main.command()
@click.argument("file")
@click.argument("patch_text")
def patch(file, patch_text):
    """Atomic patch: applied only if the model still validates (§17)."""
    m = _model(file)
    try:
        new, ops = apply_text(m, patch_text)
    except PatchError as exc:
        click.echo(f"PATCH REJECTED (rolled back): {exc}")
        raise SystemExit(1)
    for op in ops:
        click.echo(f"  {_fmt_op(op)}")
    click.echo(diff(m, new))
    click.echo("COMMITTED")


@main.command()
@click.argument("file")
def recover(file):
    """Explicit best-effort parse; reports everything it could not resolve (§21)."""
    from pathlib import Path
    text = Path(file).read_text(encoding="utf-8")
    try:
        m = load(text)
    except ParseError as exc:
        click.echo(f"ERROR: invalid XIR: {exc}")
        m, problems = recover_text(text)
        click.echo("recovered with problems:")
        for p in problems:
            click.echo(f"  - {p}")
        raise SystemExit(1)
    click.echo(f"strict parse OK: {m.name} [{m.id}]")
    click.echo(summarize(m, 2))


@main.command()
@click.argument("file")
def test(file):
    """Model-level self-test: validate, then confirm the emitted projections are stable."""
    m = _model(file)
    findings = check_model(m)
    react = E.to_react(m)
    pw = E.to_playwright(m)
    canon = to_xir(m)
    stable = diff(m, load(canon)) == "no semantic changes"
    click.echo(f"validate: {'clean' if not findings else str(len(findings)) + ' findings'}")
    click.echo(f"react: {len(react.splitlines())} lines")
    click.echo(f"playwright: {len(pw.splitlines())} lines")
    click.echo(f"round-trip: {'stable' if stable else 'UNSTABLE'}")
    for f in findings:
        click.echo(str(f))
    raise SystemExit(0 if (not findings and stable) else 1)


@main.command(name="bench")
def bench():
    """Run the agent-oriented benchmark suite (§25)."""
    from benchmarks.tasks import run_all
    for r in run_all():
        click.echo(f"{r['task']}: {r['verdict']} ({r['basis']}) {r['ms']}ms")


if __name__ == "__main__":
    main()
