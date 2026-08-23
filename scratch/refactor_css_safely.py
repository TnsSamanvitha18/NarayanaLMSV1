import re

def clean_css_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Fix malformed comment
    content = content.replace('/* /* Card Gradient Utility Variations */', '/* Card Gradient Utility Variations */')

    # 2. Normalize trailing whitespace on lines
    lines = [line.rstrip() for line in content.splitlines()]

    # 3. Collapse multiple consecutive empty lines to maximum 2 empty lines between major sections
    cleaned_lines = []
    empty_count = 0
    for line in lines:
        if not line:
            empty_count += 1
            if empty_count <= 2:
                cleaned_lines.append(line)
        else:
            empty_count = 0
            cleaned_lines.append(line)

    # 4. Remove empty lines at end of file, end with single newline
    final_content = "\n".join(cleaned_lines).rstrip() + "\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)

if __name__ == '__main__':
    clean_css_file('app/static/css/style.css')
    print("CSS safely formatted and cleaned!")
