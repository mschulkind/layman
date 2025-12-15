#!/usr/bin/env python3
"""
Validate Mermaid diagrams in markdown files.

This script extracts mermaid code blocks from markdown files and validates
their syntax. It's a basic validator that checks for common issues.
"""

import re
import sys
from pathlib import Path


def extract_mermaid_blocks(content: str) -> list[tuple[int, str]]:
    """Extract mermaid code blocks with their line numbers."""
    blocks = []
    pattern = r"```mermaid\n(.*?)```"
    
    for match in re.finditer(pattern, content, re.DOTALL):
        # Calculate line number
        line_num = content[:match.start()].count('\n') + 1
        blocks.append((line_num, match.group(1)))
    
    return blocks


def validate_mermaid_block(block: str) -> list[str]:
    """Basic validation of a mermaid block. Returns list of errors."""
    errors = []
    lines = block.strip().split('\n')
    
    if not lines:
        errors.append("Empty mermaid block")
        return errors
    
    first_line = lines[0].strip().lower()
    
    # Check for valid diagram type
    valid_types = [
        'graph', 'flowchart', 'sequencediagram', 'sequence', 
        'classDiagram', 'class', 'statediagram', 'state',
        'erdiagram', 'er', 'journey', 'gantt', 'pie',
        'requirementdiagram', 'gitgraph', 'mindmap', 'timeline',
        'c4context', 'c4container', 'c4component', 'c4dynamic',
        'sankey', 'block-beta', 'xy-chart', 'packet-beta',
        'architecture-beta',
    ]
    
    # Normalize the first line for checking
    first_word = first_line.split()[0] if first_line.split() else ""
    
    if not any(first_word.startswith(t.lower()) for t in valid_types):
        # Check if it's a subgraph or other continuation (not an error)
        if not first_word.startswith('subgraph'):
            errors.append(f"Unknown diagram type: {first_word}")
    
    # Check for balanced brackets
    open_brackets = block.count('[') + block.count('{') + block.count('(')
    close_brackets = block.count(']') + block.count('}') + block.count(')')
    
    if open_brackets != close_brackets:
        errors.append(f"Unbalanced brackets: {open_brackets} open, {close_brackets} close")
    
    return errors


def validate_file(filepath: Path) -> list[tuple[int, str]]:
    """Validate all mermaid blocks in a file. Returns list of (line, error) tuples."""
    content = filepath.read_text()
    blocks = extract_mermaid_blocks(content)
    
    all_errors = []
    for line_num, block in blocks:
        errors = validate_mermaid_block(block)
        for error in errors:
            all_errors.append((line_num, error))
    
    return all_errors


def main():
    docs_dir = Path(__file__).parent.parent / "docs"
    
    if not docs_dir.exists():
        print(f"Docs directory not found: {docs_dir}")
        sys.exit(1)
    
    all_errors = []
    files_checked = 0
    
    for md_file in docs_dir.rglob("*.md"):
        files_checked += 1
        errors = validate_file(md_file)
        
        for line_num, error in errors:
            all_errors.append((md_file, line_num, error))
    
    if all_errors:
        print("Mermaid validation errors found:")
        for filepath, line_num, error in all_errors:
            rel_path = filepath.relative_to(docs_dir.parent)
            print(f"  {rel_path}:{line_num}: {error}")
        print(f"\n{len(all_errors)} error(s) in {files_checked} file(s)")
        sys.exit(1)
    else:
        print(f"✓ All mermaid diagrams valid ({files_checked} files checked)")
        sys.exit(0)


if __name__ == "__main__":
    main()
