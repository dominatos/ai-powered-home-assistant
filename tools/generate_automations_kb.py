import yaml
import json

def generate_kb():
    with open('automations.yaml', 'r') as f:
        automations = yaml.safe_load(f)
    
    kb = "# Home Assistant Automations Knowledge Base\n\n"
    kb += "This document provides a human-readable summary of all automations currently configured in `automations.yaml`.\n\n"
    
    for auto in automations:
        if not isinstance(auto, dict):
            continue
            
        alias = auto.get('alias', 'Unnamed Automation')
        desc = auto.get('description', 'No description provided.')
        auto_id = auto.get('id', 'No ID')
        
        kb += f"## {alias}\n"
        kb += f"- **ID**: `{auto_id}`\n"
        kb += f"- **Description**: {desc}\n\n"
        
        # Triggers
        triggers = auto.get('trigger', auto.get('triggers', []))
        if triggers:
            kb += "### Triggers\n"
            if isinstance(triggers, list):
                for t in triggers:
                    platform = t.get('platform', t.get('trigger', 'unknown'))
                    kb += f"- **{platform}**: `{json.dumps({k:v for k,v in t.items() if k not in ('platform', 'trigger')})}`\n"
            else:
                kb += f"- `{json.dumps(triggers)}`\n"
        
        # Conditions
        conditions = auto.get('condition', auto.get('conditions', []))
        if conditions:
            kb += "\n### Conditions\n"
            if isinstance(conditions, list):
                for c in conditions:
                    c_type = c.get('condition', 'unknown')
                    kb += f"- **{c_type}**: `{json.dumps({k:v for k,v in c.items() if k != 'condition'})}`\n"
            else:
                kb += f"- `{json.dumps(conditions)}`\n"
                
        # Actions
        actions = auto.get('action', auto.get('actions', []))
        if actions:
            kb += "\n### Actions\n"
            if isinstance(actions, list):
                for a in actions:
                    action_type = "service/action" if ('service' in a or 'action' in a) else next(iter(a.keys()), "unknown")
                    target = a.get('service', a.get('action', 'unknown'))
                    kb += f"- **{action_type}**: `{target}` "
                    if 'entity_id' in a or ('target' in a and 'entity_id' in a['target']):
                        ent = a.get('entity_id', a.get('target', {}).get('entity_id', ''))
                        kb += f"on `{ent}` "
                    kb += "\n"
            else:
                kb += f"- `{json.dumps(actions)}`\n"
                
        kb += "\n---\n\n"
        
    with open('automations_kb.md', 'w') as f:
        f.write(kb)
        
if __name__ == '__main__':
    generate_kb()
