import re
import base64

with open(r'e:\blogAgent\drafts\2026-04-12\how-to-build-an-agentic-ml-pipeline-from-natural-language-to-production.md', 'r') as f:
    text = f.read()

mermaid_pattern = re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL)

def _mermaid_to_image_url(mermaid_code: str) -> str:
    vibrant_theme = (
        "%%{init: {'theme': 'base', 'themeVariables': { "
        "'primaryColor': '#ff9f1c', "
        "'secondaryColor': '#2ec4b6', "
        "'tertiaryColor': '#e71d36', "
        "'primaryBorderColor': '#011627', "
        "'lineColor': '#011627', "
        "'fontFamily': 'Inter, sans-serif'}}}%%\n"
    )
    if "%%{init" not in mermaid_code:
        mermaid_code = vibrant_theme + mermaid_code.strip()

    encoded = base64.urlsafe_b64encode(mermaid_code.strip().encode('utf-8')).decode('utf-8')
    return f"https://mermaid.ink/img/{encoded}?bgColor=!white"

def replace_mermaid(match):
    mermaid_code = match.group(1)
    image_url = _mermaid_to_image_url(mermaid_code)
    return f"![diagram]({image_url})"

out = mermaid_pattern.sub(replace_mermaid, text)
print("Are there any mermaid blocks left?", "```mermaid" in out)
print("Length before:", len(text), "Length after:", len(out))
# Print the first block replaced
idx = out.find("![diagram]")
if idx != -1:
    print("Found image tag:")
    print(out[idx:idx+500])
else:
    print("No image tags found!")
