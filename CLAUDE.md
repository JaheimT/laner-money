# CLAUDE.md

Read docs/roadmap.md before every task. Only work on the CURRENT
milestone, one step at a time.

## Tool use
- Create and change files with the Write and Edit tools, never with
  `cat > file <<EOF`, `python3 - <<EOF` or `sed -i`.
- Don't pipe code into an interpreter on stdin; if a script is needed,
  write it to a file first.
