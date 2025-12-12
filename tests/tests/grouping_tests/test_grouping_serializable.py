import json

from tonic_textual.classes.llm_synthesis.llm_grouping_models import LlmGrouping, GroupResponse
from tonic_textual.classes.common_api_responses.replacement import Replacement


class TestLlmGrouping:
    def test_to_dict_basic(self):
        replacement = Replacement(
            start=0,
            end=4,
            new_start=0,
            new_end=11,
            label="NAME_GIVEN",
            text="John",
            score=0.95,
            language="en",
            new_text="[NAME_GIVEN]"
        )
        grouping = LlmGrouping(
            representative="John",
            entities=[replacement]
        )

        result = grouping.to_dict()

        assert result["representative"] == "John"
        assert len(result["entities"]) == 1
        assert result["entities"][0]["text"] == "John"
        assert result["entities"][0]["label"] == "NAME_GIVEN"
        assert result["entities"][0]["start"] == 0
        assert result["entities"][0]["end"] == 4

    def test_to_dict_multiple_entities(self):
        replacements = [
            Replacement(
                start=0,
                end=4,
                new_start=0,
                new_end=11,
                label="NAME_GIVEN",
                text="John",
                score=0.95,
                language="en"
            ),
            Replacement(
                start=20,
                end=24,
                new_start=27,
                new_end=38,
                label="NAME_GIVEN",
                text="john",
                score=0.90,
                language="en"
            ),
        ]
        grouping = LlmGrouping(
            representative="John",
            entities=replacements
        )

        result = grouping.to_dict()

        assert result["representative"] == "John"
        assert len(result["entities"]) == 2
        assert result["entities"][0]["text"] == "John"
        assert result["entities"][1]["text"] == "john"

    def test_to_dict_empty_entities(self):
        grouping = LlmGrouping(
            representative="Unknown",
            entities=[]
        )

        result = grouping.to_dict()

        assert result["representative"] == "Unknown"
        assert result["entities"] == []

    def test_json_serializable(self):
        replacement = Replacement(
            start=0,
            end=4,
            new_start=0,
            new_end=11,
            label="NAME_GIVEN",
            text="John",
            score=0.95,
            language="en",
            new_text="[NAME_GIVEN]"
        )
        grouping = LlmGrouping(
            representative="John",
            entities=[replacement]
        )

        json_str = json.dumps(grouping.to_dict())
        parsed = json.loads(json_str)

        assert parsed["representative"] == "John"
        assert len(parsed["entities"]) == 1
        assert parsed["entities"][0]["text"] == "John"


class TestGroupResponse:
    def test_to_dict_single_group(self):
        replacement = Replacement(
            start=0,
            end=4,
            new_start=0,
            new_end=11,
            label="NAME_GIVEN",
            text="John",
            score=0.95,
            language="en"
        )
        grouping = LlmGrouping(
            representative="John",
            entities=[replacement]
        )
        response = GroupResponse(groups=[grouping])

        result = response.to_dict()

        assert "groups" in result
        assert len(result["groups"]) == 1
        assert result["groups"][0]["representative"] == "John"
        assert len(result["groups"][0]["entities"]) == 1

    def test_to_dict_multiple_groups(self):
        name_replacement = Replacement(
            start=0,
            end=4,
            new_start=0,
            new_end=11,
            label="NAME_GIVEN",
            text="John",
            score=0.95,
            language="en"
        )
        email_replacement = Replacement(
            start=50,
            end=70,
            new_start=57,
            new_end=77,
            label="EMAIL_ADDRESS",
            text="john@example.com",
            score=0.99,
            language="en"
        )
        name_grouping = LlmGrouping(
            representative="John",
            entities=[name_replacement]
        )
        email_grouping = LlmGrouping(
            representative="john@example.com",
            entities=[email_replacement]
        )
        response = GroupResponse(groups=[name_grouping, email_grouping])

        result = response.to_dict()

        assert len(result["groups"]) == 2
        assert result["groups"][0]["representative"] == "John"
        assert result["groups"][1]["representative"] == "john@example.com"

    def test_to_dict_empty_groups(self):
        response = GroupResponse(groups=[])

        result = response.to_dict()

        assert result["groups"] == []

    def test_json_serializable(self):
        replacement = Replacement(
            start=0,
            end=4,
            new_start=0,
            new_end=11,
            label="NAME_GIVEN",
            text="John",
            score=0.95,
            language="en"
        )
        grouping = LlmGrouping(
            representative="John",
            entities=[replacement]
        )
        response = GroupResponse(groups=[grouping])

        json_str = json.dumps(response.to_dict())
        parsed = json.loads(json_str)

        assert "groups" in parsed
        assert len(parsed["groups"]) == 1
        assert parsed["groups"][0]["representative"] == "John"

    def test_json_serializable_complex(self):
        """Test JSON serialization with multiple groups and entities."""
        replacements_group1 = [
            Replacement(
                start=0,
                end=4,
                new_start=0,
                new_end=11,
                label="NAME_GIVEN",
                text="John",
                score=0.95,
                language="en",
                new_text="[NAME_GIVEN]"
            ),
            Replacement(
                start=100,
                end=104,
                new_start=107,
                new_end=118,
                label="NAME_GIVEN",
                text="john",
                score=0.92,
                language="en",
                new_text="[NAME_GIVEN]"
            ),
        ]
        replacements_group2 = [
            Replacement(
                start=50,
                end=54,
                new_start=53,
                new_end=64,
                label="NAME_FAMILY",
                text="Smith",
                score=0.88,
                language="en",
                new_text="[NAME_FAMILY]",
                json_path="$.name.last"
            ),
        ]
        group1 = LlmGrouping(representative="John", entities=replacements_group1)
        group2 = LlmGrouping(representative="Smith", entities=replacements_group2)
        response = GroupResponse(groups=[group1, group2])

        json_str = json.dumps(response.to_dict())
        parsed = json.loads(json_str)

        assert len(parsed["groups"]) == 2
        assert parsed["groups"][0]["representative"] == "John"
        assert len(parsed["groups"][0]["entities"]) == 2
        assert parsed["groups"][1]["representative"] == "Smith"
        assert len(parsed["groups"][1]["entities"]) == 1
        assert parsed["groups"][1]["entities"][0]["json_path"] == "$.name.last"
