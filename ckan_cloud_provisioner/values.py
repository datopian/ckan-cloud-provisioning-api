from pathlib import Path

from jinja2 import Environment, FileSystemLoader
import yaml

# Configuration
base_path = Path('.') / 'templates'

base_values = yaml.load((base_path / 'aws-values.yaml').read_text())

all_kinds = dict(
    (p.stem[5:], yaml.load(p.read_text()))
    for p in 
    base_path.glob('kind-*.yaml')
)

j2_env = Environment(loader=FileSystemLoader('.'))
values_template = j2_env.get_template(str(base_path / 'templated.yaml'))

mandatory_fields = [
    'kind', 'id', 'siteTitle'
]


# Get different kind options
def kinds():
    return list(
        dict(id=k, title=v.get('provisioningKindTitle', k))
        for k, v
        in all_kinds.items()
    )


# Values check and convert
def convert_body(body):
    for field in mandatory_fields:
        if field not in body:
            raise ValueError(f'Missing mandatory field {field}')
    
    kind = body['kind']
    if kind not in all_kinds:
        raise ValueError(f'Unknown instance kind "{kind}"')
    kind_values = all_kinds[kind]

    templated_values = yaml.load(values_template.render(**body))

    values = {}
    values.update(base_values)
    values.update(kind_values)
    values.update(templated_values)
    
    del body['id']
    del body['kind']
    values.update(body)

    return values