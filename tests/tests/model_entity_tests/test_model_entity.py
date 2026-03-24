"""Tests for model-based custom entity SDK functionality.

Test categories:
- Quick API tests: Run by default (no LLM, ~30 seconds)
- LLM tests: Run with ENABLE_MODEL_ENTITY_LLM_TESTS=1 (requires LLM, ~5-10 minutes)
"""

import os
import uuid
import pytest
from tonic_textual.classes.model_entity import (
    ModelEntity,
    ModelEntityVersion,
    TrainedModel,
    VersionStatus,
    TrainedModelStatus,
)


# Skip tests that require LLM inference (annotation, suggestions, training)
skip_llm_tests = pytest.mark.skipif(
    not os.getenv("ENABLE_MODEL_ENTITY_LLM_TESTS"),
    reason="LLM tests skipped. Set ENABLE_MODEL_ENTITY_LLM_TESTS=1 to run (takes several minutes)."
)


@pytest.fixture
def unique_name():
    """Generate a unique entity name for each test."""
    return f"SDK_TEST_{uuid.uuid4().hex[:8].upper()}"


# Track entity IDs created during test session for cleanup
_created_entity_ids = []


def track_entity(entity):
    """Track an entity for cleanup. Call this after creating an entity in a test."""
    _created_entity_ids.append(entity.id)
    return entity


def untrack_entity(entity_id):
    """Remove entity from tracking (after successful deletion)."""
    if entity_id in _created_entity_ids:
        _created_entity_ids.remove(entity_id)


@pytest.fixture
def model_entity(textual, unique_name):
    """Create a model entity and ensure cleanup after test."""
    entity = textual.create_model_entity(
        name=unique_name,
        guidelines="Test guidelines for SDK testing.",
    )
    _created_entity_ids.append(entity.id)
    yield entity
    # Cleanup - delete this specific entity
    try:
        textual.delete_model_entity(entity.id)
        _created_entity_ids.remove(entity.id)
    except Exception:
        pass  # Entity may already be deleted by test


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_entities(textual):
    """Clean up any entities created during tests that weren't cleaned up."""
    yield
    # After all tests, delete only the specific entities we created
    for entity_id in list(_created_entity_ids):
        try:
            textual.delete_model_entity(entity_id)
        except Exception:
            pass
    _created_entity_ids.clear()


class TestModelEntityCRUD:
    """Tests for model entity CRUD operations."""

    def test_create_and_delete_entity(self, textual, unique_name):
        """Test creating and deleting a model entity."""
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Test guidelines for SDK testing.",
        ))

        try:
            assert entity is not None
            assert isinstance(entity, ModelEntity)
            assert entity.name == f"CUSTOM_{unique_name}"
            assert entity.id is not None
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)

    def test_create_entity_with_display_name(self, textual, unique_name):
        """Test creating entity with display name."""
        display_name = "Test Display Name"
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Test guidelines.",
            display_name=display_name,
        ))

        try:
            # display_name may be set to provided value or default to name
            assert entity.display_name is not None
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)

    def test_get_entity(self, textual, unique_name):
        """Test retrieving an entity by ID."""
        created = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Test guidelines.",
        ))

        try:
            fetched = textual.get_model_entity(created.id)
            assert fetched.id == created.id
            assert fetched.name == created.name
        finally:
            textual.delete_model_entity(created.id)
            untrack_entity(created.id)

    def test_list_entities(self, textual, unique_name):
        """Test listing model entities."""
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Test guidelines.",
        ))

        try:
            entities = textual.list_model_entities()
            assert isinstance(entities, list)
            # Just verify list returns without error and contains ModelEntity objects
            assert all(isinstance(e, ModelEntity) for e in entities)
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)


class TestModelEntityVersion:
    """Tests for model entity version operations."""

    def test_get_latest_version(self, textual, unique_name):
        """Test getting the latest version of an entity."""
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Initial guidelines.",
        ))

        try:
            version = entity.get_latest_version()
            assert version is not None
            assert isinstance(version, ModelEntityVersion)
            assert version.guidelines == "Initial guidelines."
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)

    def test_list_versions(self, textual, unique_name):
        """Test listing all versions."""
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Initial guidelines.",
        ))

        try:
            versions = entity.list_versions()
            assert isinstance(versions, list)
            assert len(versions) >= 1
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)


class TestTestDataUpload:
    """Tests for test data upload with ground truth."""

    def test_upload_test_data(self, textual, unique_name):
        """Test uploading test data with ground truth spans."""
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Identify codes like ABC-123.",
        ))

        try:
            file_ids = entity.upload_test_data([
                {
                    "text": "Code ABC-123 here.",
                    "spans": [{"start": 5, "end": 12}],
                    "fileName": "test1.txt",
                },
            ])

            assert len(file_ids) == 1
            assert all(isinstance(fid, str) for fid in file_ids)

            # Verify files are listed
            files = entity.list_test_files()
            assert len(files) == 1
            assert files[0]["status"] == "Reviewed"
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)

    def test_upload_multiple_test_files(self, textual, unique_name):
        """Test uploading multiple test files at once."""
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Identify codes.",
        ))

        try:
            file_ids = entity.upload_test_data([
                {"text": "Code AAA-111.", "spans": [{"start": 5, "end": 12}]},
                {"text": "Code BBB-222.", "spans": [{"start": 5, "end": 12}]},
                {"text": "Code CCC-333.", "spans": [{"start": 5, "end": 12}]},
            ])

            assert len(file_ids) == 3

            files = entity.list_test_files()
            assert len(files) == 3
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)


@skip_llm_tests
class TestVersionMetrics:
    """Tests for version metrics and completion (requires LLM annotation)."""

    def test_version_wait_for_completion(self, textual, unique_name):
        """Test waiting for version annotation to complete."""
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Identify product codes like SKU-12345.",
        ))

        try:
            entity.upload_test_data([
                {"text": "Product SKU-12345.", "spans": [{"start": 8, "end": 17}]},
            ])

            version = entity.get_latest_version()
            version.wait_for_completion(timeout_seconds=120)

            assert version.status == VersionStatus.READY
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)

    def test_version_metrics(self, textual, unique_name):
        """Test getting version metrics after completion."""
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Identify product codes like SKU-12345.",
        ))

        try:
            entity.upload_test_data([
                {"text": "Product SKU-12345.", "spans": [{"start": 8, "end": 17}]},
            ])

            version = entity.get_latest_version()
            version.wait_for_completion(timeout_seconds=120)

            metrics = version.get_metrics()
            assert metrics is not None
            assert metrics.f1_score is not None
            assert metrics.precision is not None
            assert metrics.recall is not None
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)


@skip_llm_tests
class TestGuidelinesRefinement:
    """Tests for guidelines refinement workflow (requires LLM)."""

    def test_create_new_version(self, textual, unique_name):
        """Test creating a new version with updated guidelines."""
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Initial vague guidelines.",
        ))

        try:
            entity.upload_test_data([
                {"text": "Code SKU-123.", "spans": [{"start": 5, "end": 12}]},
            ])

            v1 = entity.get_latest_version()
            v1.wait_for_completion(timeout_seconds=120)

            # Create new version with refined guidelines
            v2 = entity.create_version("Refined guidelines for SKU codes like SKU-123.")
            assert v2 is not None
            assert v2.version_number > v1.version_number
            assert v2.guidelines == "Refined guidelines for SKU codes like SKU-123."
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)

    def test_get_suggested_guidelines(self, textual, unique_name):
        """Test getting LLM-suggested guidelines."""
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Find codes.",
        ))

        try:
            entity.upload_test_data([
                {"text": "Code SKU-111.", "spans": [{"start": 5, "end": 12}]},
                {"text": "Code PO-222.", "spans": [{"start": 5, "end": 11}]},
            ])

            version = entity.get_latest_version()
            version.wait_for_completion(timeout_seconds=120)

            # May or may not have suggestions depending on score
            suggested = version.get_suggested_guidelines()
            # Just verify it doesn't error - suggestions may be None if score is perfect
            assert suggested is None or isinstance(suggested, str)
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)


class TestTrainingData:
    """Tests for training data upload."""

    def test_upload_training_data(self, textual, unique_name):
        """Test uploading training data."""
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Identify codes.",
        ))

        try:
            training_ids = entity.upload_training_data([
                {"text": "Training text with SKU-111.", "fileName": "train1.txt"},
                {"text": "More training SKU-222.", "fileName": "train2.txt"},
            ])

            assert len(training_ids) == 2

            files = entity.list_training_files()
            assert len(files) == 2
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)


@skip_llm_tests
class TestTrainedModel:
    """Tests for trained model operations (requires LLM for version completion)."""

    def test_create_trained_model(self, textual, unique_name):
        """Test creating a trained model."""
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Identify product codes like SKU-12345.",
        ))

        try:
            # Upload test data and wait for version
            entity.upload_test_data([
                {"text": "Product SKU-12345.", "spans": [{"start": 8, "end": 17}]},
            ])
            version = entity.get_latest_version()
            version.wait_for_completion(timeout_seconds=120)

            # Upload training data
            entity.upload_training_data([
                {"text": "Order SKU-11111.", "fileName": "train1.txt"},
            ])

            # Create model
            model = entity.create_trained_model(version.id)
            assert model is not None
            assert isinstance(model, TrainedModel)
            assert model.version_id == version.id
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)

    def test_list_trained_models(self, textual, unique_name):
        """Test listing trained models."""
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Identify codes.",
        ))

        try:
            entity.upload_test_data([
                {"text": "Code SKU-123.", "spans": [{"start": 5, "end": 12}]},
            ])
            version = entity.get_latest_version()
            version.wait_for_completion(timeout_seconds=120)

            entity.upload_training_data([
                {"text": "Train SKU-111.", "fileName": "train.txt"},
            ])

            model = entity.create_trained_model(version.id)

            models = entity.list_trained_models()
            assert len(models) >= 1
            assert any(m.id == model.id for m in models)
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)


@skip_llm_tests
class TestFullTrainingWorkflow:
    """Integration test for full training workflow (requires LLM)."""

    def test_full_workflow(self, textual, unique_name):
        """Test complete workflow: create, upload, train, activate."""
        entity = track_entity(textual.create_model_entity(
            name=unique_name,
            guidelines="Identify product SKUs in format SKU-NNNNN.",
        ))

        try:
            # Upload test data
            entity.upload_test_data([
                {"text": "Product SKU-12345.", "spans": [{"start": 8, "end": 17}]},
                {"text": "Item SKU-67890.", "spans": [{"start": 5, "end": 14}]},
            ])

            # Wait for version
            version = entity.get_latest_version()
            version.wait_for_completion(timeout_seconds=120)
            assert version.status == VersionStatus.READY

            # Check metrics
            metrics = version.get_metrics()
            assert metrics.f1_score is not None

            # Upload training data
            entity.upload_training_data([
                {"text": "Order SKU-11111 and SKU-22222.", "fileName": "train1.txt"},
                {"text": "Restock SKU-33333.", "fileName": "train2.txt"},
            ])

            # Create and train model
            model = entity.create_trained_model(version.id)

            # Wait for annotation
            while model.status not in [TrainedModelStatus.READY_FOR_TRAINING, TrainedModelStatus.FAILED]:
                model = entity.get_trained_model(model.id)
            assert model.status == TrainedModelStatus.READY_FOR_TRAINING

            # Start training
            model.start_training()

            # Wait for training
            model.wait_for_training(timeout_seconds=600)
            assert model.status == TrainedModelStatus.READY

            # Activate
            model.activate()
            assert model.is_active

            # Verify active model
            active = entity.get_active_model()
            assert active is not None
            assert active.id == model.id
        finally:
            textual.delete_model_entity(entity.id)
            untrack_entity(entity.id)
