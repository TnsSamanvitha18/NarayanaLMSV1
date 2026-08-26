import os
import re

templates_dir = r"C:\Users\adity\OneDrive\Desktop\NarayanaLMS\NarayanaLMSV1\app\templates"

# Walk through all directories and find html files
for root, dirs, files in os.walk(templates_dir):
    for name in files:
        if name.endswith(".html"):
            path = os.path.join(root, name)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find all <form ... method="POST" ...> or <form ... method="post" ...>
            # Ignore cases where csrf_token is already present immediately after the form
            
            # Simple regex matching `<form ...>` that has `method="post"` or `method="POST"`
            # We will substitute it by inserting the csrf_token hidden input
            def csrf_replacer(match):
                form_tag = match.group(0)
                if "csrf_token" in content[match.end():match.end() + 150]:
                    # Already has CSRF token nearby, skip to prevent duplicates
                    return form_tag
                return f'{form_tag}\n                <input type="hidden" name="csrf_token" value="{{{{ csrf_token() }}}}">'

            new_content = re.sub(
                r'<form[^>]+method=["\']?post["\']?[^>]*>',
                csrf_replacer,
                content,
                flags=re.IGNORECASE
            )

            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Injected CSRF token into: {os.path.relpath(path, templates_dir)}")

print("CSRF token injection completed.")
