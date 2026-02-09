"""Service for managing model-based custom entities."""

from typing import List, Optional
import requests

from tonic_textual.classes.model_entity import ModelEntity


class ModelEntityService:
    """Service for managing model-based custom entities.

    This service provides CRUD operations for model-based entities,
    which are custom NER entity types trained on user-provided data.
    """

    def __init__(self, client):
        self.client = client

    def create(
        self,
        name: str,
        guidelines: str,
        display_name: Optional[str] = None,
    ) -> ModelEntity:
        """Create a new model-based entity with initial guidelines.

        Args:
            name: Internal name for the entity (used as identifier)
            guidelines: Initial annotation guidelines for the LLM
            display_name: Optional display name for UI

        Returns:
            The newly created ModelEntity
        """
        payload = {
            "name": name,
            "guidelines": guidelines,
        }
        if display_name:
            payload["displayName"] = display_name

        response = self.client.http_post(
            "/api/model-based-entities",
            data=payload,
        )
        # Response has nested 'entity' and 'version' keys
        entity_data = response.get("entity", response)
        return ModelEntity(self.client, entity_data)

    def get(self, entity_id: str) -> ModelEntity:
        """Get a model entity by ID.

        Args:
            entity_id: The entity's unique identifier

        Returns:
            The ModelEntity object
        """
        with requests.Session() as session:
            data = self.client.http_get(
                f"/api/model-based-entities/{entity_id}",
                session=session,
            )
        return ModelEntity(self.client, data)

    def list(self) -> List[ModelEntity]:
        """List all model entities.

        Returns:
            List of all ModelEntity objects accessible to the user
        """
        with requests.Session() as session:
            # Use the custom-entities endpoint which lists all custom entities
            data = self.client.http_get(
                "/api/custom-entities",
                session=session,
            )

        # Filter to only model-based entities (entityType == "ModelBased")
        model_entities = []
        for item in data.get("records", []):
            if item.get("entityType") == "ModelBased":
                # Fetch full entity data
                entity = self.get(item["id"])
                model_entities.append(entity)

        return model_entities

    def delete(self, entity_id: str) -> None:
        """Delete a model entity.

        Args:
            entity_id: The entity's unique identifier
        """
        self.client.http_delete(f"/api/model-based-entities/{entity_id}")
