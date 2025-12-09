from dataclasses import dataclass
from pathlib import Path
import uuid
from dataclasses_json import dataclass_json
import yaml

DATA_DIR = Path(__file__).parent.parent.parent / "data"
IDEAS_FILE = DATA_DIR / "ideas.yml"


@dataclass_json
@dataclass
class Idea:
    text: str
    guid: str = ""


def list_ideas(ideas_file=IDEAS_FILE) -> list[Idea]:
    if not Path(ideas_file).exists():
        return []

    with open(ideas_file, "r", encoding="utf8") as file:
        return Idea.schema().load(yaml.safe_load(file), many=True)


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
