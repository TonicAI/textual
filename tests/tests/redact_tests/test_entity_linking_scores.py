import pytest

from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.entity_linking import EntityLinkingScore
from tonic_textual.redact_api import TextualNer


ENTITIES = [
    {
        "start": 0,
        "end": 3,
        "pythonStart": 0,
        "pythonEnd": 3,
        "label": "NAME_GIVEN",
        "text": "Ann",
        "score": 0.99,
        "language": "en",
    },
    {
        "start": 4,
        "end": 10,
        "pythonStart": 4,
        "pythonEnd": 10,
        "label": "NAME_GIVEN",
        "text": "Cheryl",
        "score": 0.98,
        "language": "en",
    },
    {
        "start": 11,
        "end": 14,
        "pythonStart": 11,
        "pythonEnd": 14,
        "label": "NAME_GIVEN",
        "text": "Bob",
        "score": 0.97,
        "language": "en",
    },
]

MATRIX = [
    [
        None,
        {"linkingConfidence": 0.895, "linkingConfidenceType": "direct"},
        {"linkingConfidence": 0.96, "linkingConfidenceType": "transitive"},
    ],
    [
        {"linkingConfidence": 0.895, "linkingConfidenceType": "direct"},
        None,
        None,
    ],
    [
        {"linkingConfidence": 0.96, "linkingConfidenceType": "transitive"},
        None,
        None,
    ],
]


@pytest.fixture
def mocked_ner(monkeypatch):
    ner = TextualNer("http://localhost", api_key="fake-key")
    requests = []

    def fake_http_post(
        url,
        params={},
        data={},
        files={},
        additional_headers={},
        timeout_seconds=None,
    ):
        requests.append({"url": url, "data": data})
        if url == "/api/synthesis/group":
            return {
                "entities": ENTITIES,
                "groups": [
                    {
                        "pii_type": "NAME_GIVEN",
                        "entity_indices": [0, 2],
                        "representative": "Ann",
                    },
                    {
                        "pii_type": "NAME_GIVEN",
                        "entity_indices": [1],
                        "representative": "Cheryl",
                    },
                ],
                "entity_linking_score_matrix": MATRIX,
            }
        return {
            "originalText": "Ann Cheryl Bob",
            "redactedText": "Kim Ada Kim",
            "usage": 3,
            "deIdentifyResults": [],
            "entityLinkingEntities": ENTITIES,
            "entityLinkingGroups": [
                {
                    "piiType": "NAME_GIVEN",
                    "entityIndices": [0, 2],
                    "representative": "Ann",
                },
                {
                    "piiType": "NAME_GIVEN",
                    "entityIndices": [1],
                    "representative": "Cheryl",
                },
            ],
            "entityLinkingScoreMatrix": MATRIX,
        }

    monkeypatch.setattr(ner.client, "http_post", fake_http_post)
    return ner, requests


def test_redact_parses_scores_and_iterates_unique_filtered_links(mocked_ner):
    ner, requests = mocked_ner

    response = ner.redact(
        "Ann Cheryl Bob",
        generator_config={"NAME_GIVEN": "GroupingSynthesis"},
        include_entity_linking_scores=True,
        entity_linking_score_limit=None,
    )

    assert requests[0]["data"]["includeEntityLinkingScores"] is True
    assert requests[0]["data"]["entityLinkingScoreLimit"] is None
    assert response.entity_linking_entities[1].text == "Cheryl"
    assert response.entity_linking_groups[0].entity_indices == [0, 2]
    assert [entity.text for entity in response.entity_linking_groups[0].entities] == [
        "Ann",
        "Bob",
    ]
    assert response.entity_linking_score_matrix[0][1] == EntityLinkingScore(
        confidence=0.895,
        confidence_type="direct",
    )

    links = list(response.iter_entity_links(min_confidence=0.90))

    assert len(links) == 1
    assert links[0].entity_a.text == "Ann"
    assert links[0].entity_b.text == "Bob"
    assert links[0].confidence == 0.96
    assert links[0].confidence_type == "transitive"
    assert list(response.iter_entity_links(confidence_type="direct"))[0].confidence == 0.895


def test_redact_omits_score_options_and_exposes_empty_iterator_by_default(monkeypatch):
    ner = TextualNer("http://localhost", api_key="fake-key")
    captured = {}

    def fake_http_post(url, data={}, **kwargs):
        captured.update(data)
        return {
            "originalText": "No names",
            "redactedText": "No names",
            "usage": 2,
            "deIdentifyResults": [],
        }

    monkeypatch.setattr(ner.client, "http_post", fake_http_post)

    response = ner.redact("No names")

    assert "includeEntityLinkingScores" not in captured
    assert "entityLinkingScoreLimit" not in captured
    assert response.entity_linking_score_matrix is None
    assert list(response.iter_entity_links()) == []


def test_group_entities_supports_indexed_groups_and_score_iteration(mocked_ner):
    ner, requests = mocked_ner
    replacements = [
        Replacement(
            start=entity["pythonStart"],
            end=entity["pythonEnd"],
            new_start=entity["pythonStart"],
            new_end=entity["pythonEnd"],
            label=entity["label"],
            text=entity["text"],
            score=entity["score"],
            language=entity["language"],
        )
        for entity in ENTITIES
    ]

    response = ner.group_entities(
        replacements,
        "Ann Cheryl Bob",
        include_entity_linking_scores=True,
        entity_linking_score_limit=None,
    )

    assert requests[0]["data"]["include_entity_linking_scores"] is True
    assert requests[0]["data"]["entity_linking_score_limit"] is None
    assert [entity.text for entity in response.entities] == ["Ann", "Cheryl", "Bob"]
    assert response.groups[0].entity_indices == [0, 2]
    assert [entity.text for entity in response.groups[0].entities] == ["Ann", "Bob"]
    assert [
        (link.entity_a.text, link.entity_b.text)
        for link in response.iter_entity_links(min_confidence=0.90)
    ] == [("Ann", "Bob")]
