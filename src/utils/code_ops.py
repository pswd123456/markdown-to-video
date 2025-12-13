import re

def extract_code(llm_output: str) -> str:
    """
    从 LLM 的回复中提取纯 Python 代码。
    支持处理 ```python ... ``` 代码块，也支持纯文本回退。
    """
    # 1. 尝试匹配 Markdown 代码块
    pattern = r"```python\s*(.*?)\s*```"
    match = re.search(pattern, llm_output, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    # 2. 如果没有代码块，尝试匹配 ``` ... ```
    pattern_generic = r"```\s*(.*?)\s*```"
    match_generic = re.search(pattern_generic, llm_output, re.DOTALL)
    if match_generic:
        return match_generic.group(1).strip()

    # 3. 都没有，假设整个文本就是代码 (风险较高，但作为回退)
    return llm_output.strip()