import os
import re

routes_dir = r"C:\Users\adity\OneDrive\Desktop\NarayanaLMS\NarayanaLMSV1\app\routes"
files = ["classes.py", "courses.py", "learners.py"]

for fname in files:
    path = os.path.join(routes_dir, fname)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Remove check_admin definition
    content = re.sub(
        r"def check_admin\(\):\s+return\s+session\.get\('admin_logged_in'\)\s*\n",
        "",
        content
    )

    # 2. Add import
    if "from app.utils.decorators import admin_required" not in content:
        # Insert after the first import line
        lines = content.splitlines()
        lines.insert(1, "from app.utils.decorators import admin_required")
        content = "\n".join(lines)

    # 3. Replace the check_admin check in routes
    # Pattern: @<bp_name>_bp.route(...) followed by def ...(): followed by if not check_admin(): ...
    # We want to insert @admin_required before the function definition and remove the check_admin check.
    
    # We can do this with a regex match.
    # Let's write a parser that scans line by line.
    lines = content.splitlines()
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("@") and "_bp.route" in line:
            # We found a route. Collect decorators
            decorators = [line]
            i += 1
            while i < len(lines) and lines[i].strip().startswith("@"):
                decorators.append(lines[i])
                i += 1
            
            # Now we must have the function definition
            if i < len(lines) and lines[i].strip().startswith("def "):
                func_def = lines[i]
                i += 1
                # Check if the next line or two contains if not check_admin():
                # Note: there might be a docstring
                docstring_lines = []
                if i < len(lines) and (lines[i].strip().startswith('"""') or lines[i].strip().startswith("'''")):
                    docstring_lines.append(lines[i])
                    i += 1
                    while i < len(lines) and not (lines[i].strip().endswith('"""') or lines[i].strip().endswith("'''")):
                        docstring_lines.append(lines[i])
                        i += 1
                    if i < len(lines):
                        docstring_lines.append(lines[i])
                        i += 1
                
                # Check for check_admin check
                has_check = False
                check_block_size = 0
                
                # Let's inspect the next few lines
                temp_i = i
                # Skip whitespace
                while temp_i < len(lines) and not lines[temp_i].strip():
                    temp_i += 1
                
                if temp_i < len(lines) and "if not check_admin():" in lines[temp_i]:
                    has_check = True
                    # How many lines to skip? Usually 2: the if statement and the return statement
                    check_block_size = temp_i - i + 2
                
                if has_check:
                    # Apply @admin_required decorator!
                    new_lines.extend(decorators)
                    new_lines.append("    @admin_required" if decorators[0].startswith("    ") else "@admin_required")
                    new_lines.append(func_def)
                    new_lines.extend(docstring_lines)
                    # Skip the check block
                    i += check_block_size
                else:
                    new_lines.extend(decorators)
                    new_lines.append(func_def)
                    new_lines.extend(docstring_lines)
            else:
                new_lines.extend(decorators)
        else:
            new_lines.append(line)
            i += 1
            
    content = "\n".join(new_lines)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        
print("Refactoring complete.")
