# Generate a CHANGELOG

1. Install Git and Python 3.8+ (on Windows, also use Git Bash), then copy this directory into your project or keep it beside your projects.
2. Run `bash changelog.sh --repo /path/to/project --output /path/to/project/CHANGELOG.md`. The default repository and output are relative to your current directory.
3. Review the four categories before release. Rerun the same command to update the generated section; keep handwritten notes outside its HTML markers.

No dependencies, model, credentials or network calls are required. `python3 generate_changelog.py` is the native Python equivalent; `--stdout` previews without writing.

## Release boundary and classification

The release boundary is the tag selected by `git describe --tags --first-parent --abbrev=0 HEAD`, including lightweight and annotated tags. A tag on a merged topic branch does not truncate unreleased mainline work. Every commit reachable from HEAD but not from the boundary is included exactly once, including merge commits and merged topic commits. The generated section records the resolved tag, boundary commit and HEAD. No first-parent tag means all reachable history. An empty repository errors. A tagged HEAD produces four empty categories. Shallow clones fail closed; fetch full history and tags explicitly before running. The generator never fetches or changes Git refs.

`feat` / `add` map to Added, `fix` to Fixed, and `remove` / `removed` / `delete` to Removed. Scopes and breaking-change `!` are supported. Ordinary subjects beginning Add / Added / Introduce, Fix / Fixed / Repair, or Remove / Removed / Delete follow the same mapping. Other subjects, including merges, reverts and docs, map to Changed. This is a transparent heuristic, not a semantic understanding of the diff: review the output. Full subjects are preserved as escaped literal Markdown, with full commit IDs. Commit framing uses Git's NUL delimiters, not a printable separator.

An existing file without exactly one valid managed section is refused, not overwritten. Generate into a new path and manually incorporate the section in that case. Content outside the managed markers is preserved. Edits inside the managed section are regenerated. Repeated runs at the same HEAD are byte-stable. Symbolic links are refused; writes use a same-directory temporary file with exclusive creation or atomic replacement. Coordinate simultaneous human edits rather than relying on the change check as a multi-writer lock.

## Verification

Run `python3 -m unittest discover -s . -p test_changelog.py -v` from this directory. Tests create disposable local repositories only, disable hooks/signing and cover first-parent boundaries with tagged topic merges, annotated/lightweight tags, shallow/empty history, framing, literal Markdown, all categories, stable reruns and handwritten-note preservation.

`samples/CHANGELOG.md` is actual generated output from a public GitHub repository. Its pinned source and reproduction commands are in `samples/SOURCE.md`. AI-assisted implementation. No paid model or external API is used by the tool.
