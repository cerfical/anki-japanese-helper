from typing import Dict

from aqt import mw, utils

from anki.notes import Note as AnkiNote

ADDON_ID = mw.addonManager.addonFromModule(__name__)


type Note = Dict[str, str]


def decks() -> list[str]:
    return mw.col.decks.all_names()


def noteTypes() -> list[str]:
    return [n["name"] for n in mw.col.models.all()]


def anyNotes(deck: str, note_type: str, *fields: tuple[str, str]) -> bool:
    return len(findNotes(deck, note_type, *fields)) > 0


def findNotes(deck: str, note_type: str, *fields: tuple[str, str]) -> list[Note]:
    deck_note_sel = f'deck:"{deck}" note:"{note_type}"'
    field_sel = " ".join(map(lambda f: f'{f[0]}:"{f[1]}"', fields))

    note_ids = mw.col.find_notes(deck_note_sel + " " + field_sel)
    notes = []

    for n in map(mw.col.get_note, note_ids):
        note = {}
        for f in findFields(note_type):
            note[f] = n[f]
        notes.append(note)
    return notes


def findFields(note_type: str) -> list[str]:
    field_names = []
    for field in _noteTypeByName(note_type)["flds"]:
        field_names.append(field["name"])
    return field_names


def uploadNote(note: Note, deck: str, note_type: str) -> bool:
    n = AnkiNote(mw.col, _noteTypeIdByName(note_type))
    for field, value in note.items():
        n[field] = value

    deck_id = _deckIdByName(deck)
    if mw.col.add_note(n, deck_id):
        mw.col.autosave()
        mw.reset()
        return True
    return False


def uploadMedia(filename: str, data: bytes) -> str:
    return mw.col.media.writeData(filename, data)


def notify(message: str):
    utils.tooltip(message)


def _deckIdByName(name: str) -> int:
    return mw.col.decks.id(name)


def _noteTypeIdByName(name: str) -> int:
    return _noteTypeByName(name)["id"]


def _noteTypeByName(name: str) -> AnkiNote:
    return mw.col.models.byName(name)
