from jinja2.sandbox import SandboxedEnvironment
from jinja2 import meta, exceptions

env = SandboxedEnvironment()

def extract_required_variables(content: str):
    """
    Return a list of undeclared variables referenced in the template content.
    """
    try:
        ast = env.parse(content)
        return sorted(list(meta.find_undeclared_variables(ast)))
    except exceptions.TemplateSyntaxError as e:
        raise

def render_content(content: str, template_vars: dict) -> str:
    """
    Render Jinja2 template with strict undefined (will raise on missing).
    """
    tpl = env.from_string(content)
    return tpl.render(**template_vars)
