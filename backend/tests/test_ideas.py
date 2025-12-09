from onyo_backend.ideas import (
    Idea,
    TextPart,
    add_idea,
    delete_idea,
    list_ideas,
    save_ideas,
    split_text_parts,
)


def test_save_list_ideas(tmp_path):
    ideas_file = tmp_path / "ideas.yml"
    ideas = [
        Idea("idea1", guid="1"),
        Idea("idea2", guid="2"),
    ]
    save_ideas(ideas, ideas_file=ideas_file)
    saved_ideas = list_ideas(ideas_file)
    assert saved_ideas == ideas


def test_add_idea(tmp_path):
    ideas_file = tmp_path / "ideas.yml"
    ideas = [
        Idea("idea1", guid="1"),
        Idea("idea2", guid="2"),
    ]
    save_ideas(ideas, ideas_file=ideas_file)

    # when
    add_idea(Idea("idea 3"), ideas_file=ideas_file)
    saved_ideas = list_ideas(ideas_file)

    # then
    assert len(saved_ideas) == 3
    assert saved_ideas[:2] == ideas
    assert saved_ideas[2].text == "idea 3"
    assert saved_ideas[2].guid != "", "Should generate GUID"


def test_delete_idea(tmp_path):
    ideas_file = tmp_path / "ideas.yml"
    ideas = [
        Idea("idea1", guid="1"),
        Idea("idea2", guid="2"),
    ]
    save_ideas(ideas, ideas_file=ideas_file)

    # when
    delete_idea("1", ideas_file=ideas_file)
    saved_ideas = list_ideas(ideas_file)

    # then
    assert saved_ideas == ideas[1:]


def test_split_text_parts():
    parts = split_text_parts(
        "aba https://www.delallo.com/recipe/baked-tuscan-gnocchi/ - tried, needs more tomato base, fresh https://www.delallo.com tomatoes"
    )
    assert parts == [
        TextPart(text="aba ", type="text"),
        TextPart(
            text="https://www.delallo.com/recipe/baked-tuscan-gnocchi/", type="link"
        ),
        TextPart(text=" - tried, needs more tomato base, fresh ", type="text"),
        TextPart(text="https://www.delallo.com", type="link"),
        TextPart(text=" tomatoes", type="text"),
    ]
