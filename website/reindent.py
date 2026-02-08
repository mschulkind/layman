import sys
import re

def reindent_html(content):
    # This is a very simple HTML prettifier for this specific case
    # Since the file is already flattened, we can try to re-indent it.
    # However, a regex-based approach might be risky.
    # Let's try to just use a proper tool if available or a slightly better regex.
    
    # Actually, the user just wants the file to look valid and be indented.
    # I'll use a simple indent tracker.
    
    lines = []
    indent_level = 0
    indent_size = 2
    
    # Basic tags that don't need closing or are usually one-liners in this file
    void_tags = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 
                 'link', 'meta', 'param', 'source', 'track', 'wbr', '!DOCTYPE'}
    
    # Split by tags but keep the tags
    parts = re.split('(<[^>]+>)', content)
    
    current_line = ""
    
    for part in parts:
        if not part:
            continue
        
        if part.startswith('<'):
            # It's a tag
            tag_match = re.match(r'<(/?)(\w+)', part)
            if tag_match:
                is_closing = tag_match.group(1) == '/'
                tag_name = tag_match.group(2).lower()
                
                if is_closing:
                    indent_level = max(0, indent_level - 1)
                    if current_line.strip():
                        lines.append(current_line)
                    lines.append(' ' * (indent_level * indent_size) + part)
                    current_line = ""
                else:
                    if current_line.strip():
                        lines.append(current_line)
                    lines.append(' ' * (indent_level * indent_size) + part)
                    if tag_name not in void_tags and not part.endswith('/>'):
                        indent_level += 1
                    current_line = ""
            else:
                # Comment or doctype
                if current_line.strip():
                    lines.append(current_line)
                lines.append(' ' * (indent_level * indent_size) + part)
                current_line = ""
        else:
            # It's text
            text = part.strip()
            if text:
                if current_line:
                    current_line += " " + text
                else:
                    current_line = ' ' * (indent_level * indent_size) + text
    
    if current_line.strip():
        lines.append(current_line)
        
    return '\n'.join(lines)

# But wait, the file has blocks like <style> where we shouldn't just split by tags.
# Let's use a better approach.

def clean_and_format(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 2. Remove class=""
    content = re.sub(r'class="\s*"', '', content)
    # Remove extra spaces inside tags after removing class
    content = re.sub(r'  +', ' ', content)
    content = re.sub(r' >', '>', content)

    # I will use a simple heuristic for indentation because the file is mostly flat.
    # But since it's a large file, I'll use beautifulsoup if available, 
    # or just do a decent job with regex.
    
    return content

# Read file
with open('/home/matt/code/layman/site/index.html', 'r') as f:
    content = f.read()

# Remove empty class attributes
content = re.sub(r'class="\s*"', '', content)
# Ensure no fade-in remains in class names (per request)
content = re.sub(r'fade-in\s*', '', content)

# Write it back temporarily to use a formatter if possible, or just use python to format
# Let's try to use 'npx prettier --write' which is likely available since package.json/pnpm-lock.yaml exists.
