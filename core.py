import yaml
try:  # only load with base loader for security reasons
    from yaml.cyaml import CBaseLoader as YAMLLoader
except ImportError:
    from yaml import BaseLoader as YAMLLoader 

import re

# the result of load_rules
class Rulesets(dict):
    @property
    def names(self):
        """The names of the rules."""
        return sorted(self.keys())


# a set of rules (typing)
Ruleset = list[tuple[re.Pattern, str]]


def load_rules(file: str | int) -> Rulesets:
    """Loads one or more rule sets for transcribing text from a yaml file."""

    with open(file, 'rt', encoding='utf-8') as f:
        raw_yaml = yaml.load_all(f.read(), YAMLLoader)

    parsed = Rulesets()
    unnamed = 0

    for ruleset in raw_yaml:
        if not 'rules' in ruleset:
            continue

        if 'name' in ruleset:
            name = ruleset['name']
        else:
            name = "Unnamed ruleset #" + str(unnamed + 1)
            unnamed += 1

        rules = []
        for rule in ruleset['rules']:
            for regex, replacement in rule.items():
                rules.append( (re.compile(regex), replacement) )

        parsed[name] = rules
        
    return parsed


def parse_text(text: str, rules: Ruleset): 
    """Parses a given text with a given set of rules (regex pattern -> replacement)"""

    for regex, replacement in rules:
        text = re.sub(regex, replacement, text)
    
    return text
