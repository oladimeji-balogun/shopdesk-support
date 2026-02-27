from jinja2 import Environment, FileSystemLoader

def load_prompt(filename: str, **kwargs) -> str: 
    file_system_loader = FileSystemLoader(searchpath="prompts")
    environment = Environment(loader=file_system_loader)
    
    template = environment.get_template(name=f"{filename}.md")
    prompt = template.render(**kwargs)
    return prompt

