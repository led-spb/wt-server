from typing import List
import click
import difflib
from dataclasses import dataclass
from flask import current_app
from flask.cli import AppGroup
from ..models import db
from ..models.word import Word, Accent, Spelling
from ..services.words import WordService
from marshmallow import Schema, fields, post_load

imports_commands = AppGroup('import', help='Import data')


@dataclass
class ImportWord:
    fullword: str
    context: str|None
    spellings: List[str]

class WordImportSchema(Schema):
    fullword = fields.String(required=True)
    context = fields.String(required=False, allow_none=True)
    spellings = fields.List(fields.String, required=False)

    @post_load
    def make_instance(self, data, **kwargs):
        return ImportWord(**data)


class CSVReader:
    def __init__(self, filename):
        self.filename = filename
        self.fp = None
        self.schema = WordImportSchema()

    def __enter__(self):
        self.fp = open(self.filename, 'rt', encoding='utf-8')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fp:
            self.fp.close()
    
    def __iter__(self):
        return self

    def split_csv(self, line: str) -> List[str]:
        line = line.strip()
        for s in [',', '|', '/']:
            line = line.replace(s, ';')
        return line.split(';')

    def __next__(self) -> ImportWord:
        assert self.fp is not None

        while True:
            data = self.split_csv(next(self.fp))

            word = data[0].strip()
            if word == '':
                continue

            context = next(iter(data[1:2]), '').strip()
            spellings = [item.strip() for item in data[2:] if item.strip() !='']

            #return self.schema.load({'fullword': word, 'context': None if context == '' else context, 'spellings': spellings})
            return ImportWord(
                fullword=word,
                context=None if context == '' else context,
                spellings=spellings
            )
        pass


@imports_commands.command('words', help='Import words from csv file')
@click.option('--level', type=click.INT, default=20)
@click.option('--skip-exists', is_flag=True, default=False)
@click.option('--tag', 'tags', multiple=True, type=click.INT)
@click.option('--rule', 'rules', multiple=True, type=click.INT)
@click.argument('filename', type=str)
def import_word(filename, level, skip_exists, tags, rules):
    with CSVReader(filename) as reader:
        for data in reader:
            word = create_word(data, level, skip_exists)

            if len(tags) > 0:
                if word.tags is None:
                    word.tags = tags
                else:
                    word.tags = list(set(word.tags + list(tags)))

            if len(rules) > 0:
                if word.rules is None:
                    word.rules = rules
                else:
                    word.rules = list(set(word.rules + list(rules)))


            db.session.add(word)
            db.session.commit()
        pass
    return


def is_vowel(chr) -> bool:
    return chr.lower() in ['а','е','ё','и','о','у','ы','э','ю','я']


def create_word(data :ImportWord, level :int, skip_exists :bool):
    word = WordService.find_by_name(data.fullword.lower(), data.context)
    if word is not None and skip_exists:
        return word

    if word is None:
        current_app.logger.warning(f'import word {data.fullword} ({data.context})')
        word = Word(
            fullword = data.fullword.lower(),
            context = data.context,
            level = level
        )

    create_accent(word, data.fullword)
    for sp in data.spellings:
        create_spelling(word, sp.strip())
    return word


def create_accent(word :Word, variant :str) -> None:
    accent_position = next(
        (idx for idx, chr in enumerate(variant) if chr.isupper() and is_vowel(chr)), None)
    if accent_position is not None:
        acc_positions = [acc.position for acc in word.accents]
        if accent_position not in acc_positions:
            word.accents.append(
                Accent(word_id=word.id, position=accent_position)
            )
    pass

def create_spelling(word :Word, variant :str) -> Word:
    if variant == '':
        return word

    matcher = difflib.SequenceMatcher()
    matcher.set_seqs(word.fullword, variant)

    for action in matcher.get_opcodes():
        if action[0] == 'equal':
            continue

        variant1 = word.fullword[action[1]:action[2]]
        variant2 = variant[action[3]:action[4]]
        
        spelling = Spelling(
            position=action[1],
            length=action[2]-action[1],
            variants=[
                '_' if variant1 == '' else variant1,
                '_' if variant2 == '' else variant2
            ]
        )
        add_word_spelling(word, spelling)
    return word

def add_word_spelling(word :Word, spelling :Spelling):
    for item in word.spellings:
        if item.position == spelling.position and item.length == spelling.length:
            new_variants = list(set(item.variants + spelling.variants))
            item.variants = new_variants
            return word
    word.spellings.append(spelling)
