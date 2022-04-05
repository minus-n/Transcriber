from collections import namedtuple
import yaml
try:
    from yaml.cyaml import CBaseLoader as YAMLLoader
except ImportError:
    from yaml import BaseLoader as YAMLLoader 
import re

TranscriptionTables = namedtuple('TranscribtionTables', ('available', 'tables'))

def load(file):
    with open(file, 'rt', encoding='utf-8') as f:
        transcriptions = yaml.load_all(f.read(), YAMLLoader)

        parsed_transcriptions = dict()

        for transcription in transcriptions:
            name = transcription['name']
            rules = list()
            for rule in transcription['rules']:
                for regex, replacement in rule.items():
                    rules.append((re.compile(regex), replacement))
            
            parsed_transcriptions[name] = rules
            
        return TranscriptionTables(
            parsed_transcriptions.keys(),  # make all the names accessable as tables.name
            parsed_transcriptions
        )


