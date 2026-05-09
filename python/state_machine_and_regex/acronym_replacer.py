import re

acronyms = {
    'Computer Sciences': 'CS',
    'Artificial Intelligence': 'AI'
}

def replace_single(acronym):
    count = 0
    def replace(match):
        nonlocal count
        count +=1
        if count == 1:
            return f"{match.group(0)} ({acronym})"
        else:
            return acronym
    return replace

def acronym_replacer(text: str, acronyms: dict):
    for mean, acronym in acronyms.items():
        replacer = replace_single(acronym)
        pattern = re.compile(re.escape(mean), re.IGNORECASE)
        text = pattern.sub(replacer, text)
    return text

with open("sample_text.txt",'r') as f:
    text = f.read()
    print(acronym_replacer(text,acronyms))