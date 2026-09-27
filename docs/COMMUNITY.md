# Community

XIR is a specification and a compiler, and both get better when the people using them
argue about them. Everything below is a real link, and nothing is aspirational.

## Where things happen

| Venue | For |
| --- | --- |
| [Issues](https://github.com/ZakLr/XIR/issues) | bugs, and features small enough to state in a sentence |
| [Discussions](https://github.com/ZakLr/XIR/discussions) | "how should this work?", ontology design, showing your models |
| [Contributing](../CONTRIBUTING.md) | the loop from a question to a merged change |

When a question is really a bug, open an issue. When it is really a design question,
open a discussion. When it is "I think this premise is wrong", start a discussion and
be blunt — the premise is the most likely thing to be wrong.

## Before you open anything

Two things make issues much easier to act on:

1. **Run `xir validate` and paste the output.** A model that does not validate cannot
   produce a trustworthy answer, so the first question is always whether it validates.
2. **Say which claim you expected and which you got.** "It is wrong" is not actionable.
   "Tracing `archiveProject` says no confirmation is required, but
   `spec/validation.md` says destructive actions need it" is.

## Good first issues

- Model a real product and report where the ontology forced a lie.
- Find a validation rule that produces a false positive, or misses a real inconsistency.
- Improve an emitter so its output is something you would actually ship.
- Port an emitter, or add a new projection target.
- Write the missing part of a spec that you had to guess at.

## The one thing that would help most

A **blinded agent trial**: the same task, the same base model, run with and without the
XIR model in context. Not a demo, not an opinion — a real number. Everything currently
marked `SIMULATED` or `INFERRED` in [the benchmark report](../benchmarks/report.md) exists
because nobody has run this yet. If you can run it,
[open an issue](https://github.com/ZakLr/XIR/issues) before you start, so the protocol
can be agreed in advance rather than argued about afterwards.

## Conduct

Assume the other person read the spec. Be concrete. Disagree about the model, not the
person who wrote it. No condescension about anyone's tooling, including the choice to
use an LLM at all — the question is whether XIR helps, and that is answerable with
evidence.

## Recognising contributors

Contributors appear in [the changelog](../CHANGELOG.md) and in the commit history. If you
contributed something substantial and want credit beyond that, say so in the PR and it
will be recorded in the changelog entry for the release.
