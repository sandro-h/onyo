from dataclasses import dataclass, field
from pathlib import Path
import re
import uuid
from dataclasses_json import dataclass_json
import yaml

DATA_DIR = Path(__file__).parent.parent.parent / "data"
IDEAS_FILE = DATA_DIR / "ideas.yml"
URL_PATTERN = re.compile(r"https?://[^\s]+")


@dataclass_json
@dataclass
class Idea:
    text: str
    guid: str = ""


@dataclass_json
@dataclass
class TextPart:
    text: str
    type: str = "text"


@dataclass_json
@dataclass
class IdeaForHtml:
    parts: list[TextPart] = field(default_factory=list)
    guid: str = ""


def list_ideas(ideas_file=IDEAS_FILE) -> list[Idea]:
    if not Path(ideas_file).exists():
        return []

    with open(ideas_file, "r", encoding="utf8") as file:
        return Idea.schema().load(yaml.safe_load(file), many=True)


def list_ideas_for_html(ideas_file=IDEAS_FILE) -> list[IdeaForHtml]:
    ideas = list_ideas(ideas_file)
    return [
        IdeaForHtml(
            guid=i.guid,
            parts=split_text_parts(i.text),
        )
        for i in ideas
    ]


def split_text_parts(text: str):
    parts = []
    k = 0
    for m in URL_PATTERN.finditer(text):
        if m.start() > k:
            parts.append(TextPart(text[k : m.start()]))
        parts.append(TextPart(m.group(0), type="link"))
        k = m.end()

    if k < len(text):
        parts.append(TextPart(text[k:]))

    return parts


def save_ideas(ideas: list[Idea], ideas_file=IDEAS_FILE):
    with open(ideas_file, "w", encoding="utf8") as file:
        data = Idea.schema().dump(ideas, many=True)
        yaml.safe_dump(data, file)


def add_idea(idea: Idea, ideas_file=IDEAS_FILE):
    ideas = list_ideas(ideas_file)
    idea.guid = str(uuid.uuid4())
    ideas.append(idea)
    save_ideas(ideas, ideas_file)


def delete_idea(guid_to_delete: str, ideas_file=IDEAS_FILE):
    ideas = list_ideas(ideas_file)
    ideas = [i for i in ideas if i.guid != guid_to_delete]
    save_ideas(ideas, ideas_file)
