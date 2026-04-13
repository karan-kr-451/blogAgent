import re
body = r'Observe $\rightarrow$ Think $\rightarrow$ Act $\rightarrow$ Observe'
inline_math_pattern = re.compile(r'(?<!\$)\$([^$\n]+?)\$(?!\$)')
print(inline_math_pattern.sub(r'{% katex inline %}\1{% endkatex %}', body))
