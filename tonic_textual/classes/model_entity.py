"""Model-based custom entity classes for the Tonic Textual SDK."""

from dataclasses import dataclass
from enum import Enum
from time import sleep
from typing import Dict, List, Optional
import io
import json
import os
import requests


class ModelEntityStatus(str, Enum):
    """Status of a model-based entity."""
    TEST_DATA_SETUP = "TestDataSetup"
    GUIDELINES_REFINEMENT = "GuidelinesRefinement"
    PRE_TRAINING = "PreTraining"
    TRAINING = "Training"
    READY = "Ready"


class VersionStatus(str, Enum):
    """Status of a model entity version."""
    ANNOTATING = "Annotating"
    QUEUED_FOR_SUGGESTIONS = "QueuedForSuggestions"
    GENERATING_SUGGESTIONS = "GeneratingSuggestions"
    READY = "Ready"
    FAILED = "Failed"


class TrainedModelStatus(str, Enum):
    """Status of a trained model."""
    WAITING_FOR_FILES = "WaitingForFiles"
    ANNOTATING = "Annotating"
    READY_FOR_TRAINING = "ReadyForTraining"
    TRAINING = "Training"
    READY = "Ready"
    FAILED = "Failed"


@dataclass
class Span:
    """An entity span with character offsets."""
    start: int
    end: int
    text: Optional[str] = None

    def to_dict(self) -> Dict:
        d = {"start": self.start, "end": self.end}
        if self.text:
            d["text"] = self.text
        return d


@dataclass
class VersionMetrics:
    """Performance metrics for a model entity version."""
    f1_score: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    entity_count: int

    @classmethod
    def from_dict(cls, data: Dict) -> "VersionMetrics":
        return cls(
            f1_score=data.get("f1Score"),
            precision=data.get("precisionScore"),
            recall=data.get("recallScore"),
            entity_count=data.get("entityCount", 0),
        )


@dataclass
class FileMetrics:
    """Per-file performance metrics."""
    file_id: str
    file_name: str
    f1_score: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    num_entities: int

    @classmethod
    def from_dict(cls, data: Dict) -> "FileMetrics":
        return cls(
            file_id=data.get("fileId", ""),
            file_name=data.get("fileName", ""),
            f1_score=data.get("f1Score"),
            precision=data.get("precisionScore"),
            recall=data.get("recallScore"),
            num_entities=data.get("numEntities", 0),
        )


class ModelEntityError(Exception):
    """Base exception for model entity operations."""
    pass


class AnnotationTimeoutError(ModelEntityError):
    """Raised when annotation takes too long."""
    pass


class TrainingFailedError(ModelEntityError):
    """Raised when model training fails."""
    pass


class TrainedModel:
    """A trained NER model for a model entity."""

    def __init__(self, client, entity_id: str, data: Dict):
        self._client = client
        self._entity_id = entity_id
        self.id = data["id"]
        self.number = data.get("number", 0)
        self.version_id = data.get("versionId")
        self.status = TrainedModelStatus(data["status"])
        self.is_active = data.get("isActive", False)
        self.f1_score = data.get("benchmarkScore")
        self._data = data

    def start_training(self) -> None:
        """Start the model training job."""
        self._client.http_post(
            f"/api/model-based-entities/{self._entity_id}/training/models/{self.id}/train"
        )

    def activate(self) -> None:
        """Set this model as the active model for the entity."""
        self._client.http_post(
            f"/api/model-based-entities/{self._entity_id}/training/models/{self.id}/activate"
        )
        self.is_active = True

    def get_status(self) -> TrainedModelStatus:
        """Refresh and return current training status."""
        with requests.Session() as session:
            data = self._client.http_get(
                f"/api/model-based-entities/{self._entity_id}/training/models/{self.id}",
                session=session,
            )
        self.status = TrainedModelStatus(data["status"])
        self.f1_score = data.get("benchmarkScore")
        self.is_active = data.get("isActive", False)
        return self.status

    def wait_for_training(
        self,
        timeout_seconds: int = 3600,
        poll_interval: int = 30,
    ) -> "TrainedModel":
        """
        Wait for training to complete.

        Args:
            timeout_seconds: Max time to wait (default 1 hour)
            poll_interval: Seconds between status checks

        Returns:
            Updated model object

        Raises:
            TimeoutError: If not complete within timeout
            TrainingFailedError: If training fails
        """
        elapsed = 0
        while elapsed < timeout_seconds:
            status = self.get_status()
            if status == TrainedModelStatus.READY:
                return self
            if status == TrainedModelStatus.FAILED:
                raise TrainingFailedError(f"Training failed for model {self.id}")
            sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(
            f"Training did not complete within {timeout_seconds} seconds. "
            f"Current status: {self.status}"
        )


class ModelEntityVersion:
    """A version of annotation guidelines for a model entity."""

    def __init__(self, client, entity_id: str, data: Dict):
        self._client = client
        self._entity_id = entity_id
        self.id = data["id"]
        self.version_number = data.get("versionNumber", 1)
        self.guidelines = data.get("guidelines", "")
        self.status = VersionStatus(data["status"])
        self._data = data

    def get_metrics(self) -> VersionMetrics:
        """Get overall performance metrics for this version."""
        return VersionMetrics.from_dict(self._data)

    def get_per_file_metrics(self) -> List[FileMetrics]:
        """Get per-file performance metrics."""
        files = self._data.get("files", [])
        return [FileMetrics.from_dict(f) for f in files]

    def get_suggested_guidelines(self) -> Optional[str]:
        """Get LLM-suggested guidelines improvements (if ready)."""
        with requests.Session() as session:
            data = self._client.http_get(
                f"/api/model-based-entities/{self._entity_id}/versions/{self.id}/suggested-guidelines",
                session=session,
            )
        if data and data.get("status") == "Ready":
            return data.get("guidelines")
        return None

    def retry_annotation(self) -> None:
        """Retry failed annotation jobs for this version."""
        self._client.http_post(
            f"/api/model-based-entities/{self._entity_id}/versions/{self.id}/retry"
        )

    def _refresh(self) -> None:
        """Refresh version data from server."""
        with requests.Session() as session:
            data = self._client.http_get(
                f"/api/model-based-entities/{self._entity_id}/versions/{self.id}",
                session=session,
            )
        self.status = VersionStatus(data["status"])
        self._data = data

    def wait_for_completion(
        self,
        timeout_seconds: int = 300,
        poll_interval: int = 5,
    ) -> "ModelEntityVersion":
        """
        Wait for annotation and suggestions to complete.

        Args:
            timeout_seconds: Max time to wait
            poll_interval: Seconds between status checks

        Returns:
            Updated version object

        Raises:
            TimeoutError: If not complete within timeout
        """
        elapsed = 0
        while elapsed < timeout_seconds:
            self._refresh()
            if self.status == VersionStatus.READY:
                return self
            if self.status == VersionStatus.FAILED:
                raise AnnotationTimeoutError(
                    f"Version {self.id} failed. Check error details."
                )
            sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(
            f"Version did not complete within {timeout_seconds} seconds. "
            f"Current status: {self.status}"
        )


class ModelEntity:
    """A model-based custom entity for NER.

    This class represents a custom entity type that uses ML models for detection.
    It supports the full workflow of:
    1. Uploading test data with ground truth annotations
    2. Iterating on guidelines based on LLM suggestions
    3. Training a model on annotated data
    4. Activating the model for use in datasets

    Examples
    --------
    >>> from tonic_textual.redact_api import TextualNer
    >>> textual = TextualNer()
    >>> entity = textual.create_model_entity(
    ...     name="PRODUCT_CODE",
    ...     guidelines="Identify product codes like ABC-1234"
    ... )
    >>> entity.upload_test_data([
    ...     {"text": "Order ABC-1234", "spans": [{"start": 6, "end": 14}]}
    ... ])
    """

    def __init__(self, client, data: Dict):
        self._client = client
        self.id = data["id"]
        self.name = data["name"]
        self.display_name = data.get("displayName")
        self.status = ModelEntityStatus(data["status"])
        self._data = data

    def _refresh(self) -> None:
        """Refresh entity data from server."""
        with requests.Session() as session:
            data = self._client.http_get(
                f"/api/model-based-entities/{self.id}",
                session=session,
            )
        self.status = ModelEntityStatus(data["status"])
        self._data = data

    # --- Version Management ---

    def create_version(self, guidelines: str) -> ModelEntityVersion:
        """Create a new version with updated guidelines.

        This triggers LLM annotation of all test files with the new guidelines.

        Args:
            guidelines: The annotation guidelines text

        Returns:
            The newly created version
        """
        data = self._client.http_post(
            f"/api/model-based-entities/{self.id}/versions",
            data={"guidelines": guidelines},
        )
        return ModelEntityVersion(self._client, self.id, data)

    def get_version(self, version_id: str) -> ModelEntityVersion:
        """Get a specific version by ID."""
        with requests.Session() as session:
            data = self._client.http_get(
                f"/api/model-based-entities/{self.id}/versions/{version_id}",
                session=session,
            )
        return ModelEntityVersion(self._client, self.id, data)

    def get_latest_version(self) -> ModelEntityVersion:
        """Get the most recent version."""
        versions = self.list_versions()
        if not versions:
            raise ModelEntityError(f"No versions found for entity {self.id}")
        return versions[-1]

    def list_versions(self) -> List[ModelEntityVersion]:
        """List all versions."""
        with requests.Session() as session:
            data = self._client.http_get(
                f"/api/model-based-entities/{self.id}/versions",
                session=session,
            )
        # API returns {"versions": {1: "id1", 2: "id2", ...}}
        version_map = data.get("versions", {})
        versions = []
        for version_num in sorted(version_map.keys(), key=int):
            version_id = version_map[version_num]
            version = self.get_version(version_id)
            versions.append(version)
        return versions

    # --- Test Data (Ground Truth) ---

    def upload_test_data(
        self,
        files: List[Dict],
        wait_for_processing: bool = True,
        processing_timeout: int = 120,
    ) -> List[str]:
        """
        Upload test files with ground-truth annotations.

        This method:
        1. Creates a temp .txt file for each entry
        2. Uploads via POST /test/files (multipart)
        3. Waits for file processing to complete
        4. Saves ground truth via POST /test/files/{fileId}

        Args:
            files: List of dicts with keys:
                - fileName (optional): Name for the file (auto-generated if not provided)
                - text: The text content
                - spans: List of dicts with start/end keys
            wait_for_processing: Wait for files to be ready before saving ground truth
            processing_timeout: Max seconds to wait for each file

        Returns:
            List of created file IDs
        """
        file_ids = []
        files_with_spans = []

        # First, upload all files
        for i, file_data in enumerate(files):
            text = file_data["text"]
            spans = file_data.get("spans", [])
            file_name = file_data.get("fileName", f"test_file_{i}.txt")

            # Upload the file
            file_id = self._upload_text_as_file(text, file_name, is_training=False)
            file_ids.append(file_id)

            if spans:
                files_with_spans.append((file_id, spans))

        # Then save ground truth (after files are ready)
        if files_with_spans and wait_for_processing:
            # Wait for files to be processed before saving ground truth
            self._wait_for_files_ready(file_ids, timeout_seconds=processing_timeout)

        for file_id, spans in files_with_spans:
            self._save_ground_truth(file_id, spans)

        return file_ids

    def _wait_for_files_ready(self, file_ids: List[str], timeout_seconds: int = 120) -> None:
        """Wait for files to be ready for review."""
        ready_statuses = {"ReadyForReview", "ReviewInProgress", "Reviewed"}
        elapsed = 0
        poll_interval = 2

        while elapsed < timeout_seconds:
            with requests.Session() as session:
                files = self._client.http_get(
                    f"/api/model-based-entities/{self.id}/test/files",
                    session=session,
                )

            all_ready = True
            for f in files:
                if f["id"] in file_ids and f["status"] not in ready_statuses:
                    all_ready = False
                    break

            if all_ready:
                return

            sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Files not ready within {timeout_seconds} seconds")

    def upload_test_data_jsonl(self, file_path: str) -> List[str]:
        """
        Upload test data from a JSONL file.

        Each line should be a JSON object with:
        - text: The text content
        - spans: List of {start, end} objects
        - fileName (optional): Name for the file

        Args:
            file_path: Path to the JSONL file

        Returns:
            List of created file IDs
        """
        files = []
        with open(file_path, "r") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                if "fileName" not in data:
                    data["fileName"] = f"test_file_{i}.txt"
                files.append(data)
        return self.upload_test_data(files)

    def upload_test_file(
        self,
        file_path: str,
        spans: Optional[List[Dict]] = None,
    ) -> str:
        """
        Upload a single test file from disk.

        Args:
            file_path: Path to the file (.txt, .pdf, .docx, etc.)
            spans: Optional ground truth annotations to save after upload

        Returns:
            Created file ID
        """
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            file_id = self._upload_file(f, file_name, is_training=False)

        if spans:
            self._save_ground_truth(file_id, spans)

        return file_id

    def _upload_text_as_file(self, text: str, file_name: str, is_training: bool) -> str:
        """Upload text content as a .txt file."""
        # Ensure .txt extension
        if not file_name.endswith(".txt"):
            file_name = file_name + ".txt"

        # Create in-memory file
        file_obj = io.BytesIO(text.encode("utf-8"))
        return self._upload_file(file_obj, file_name, is_training)

    def _upload_file(self, file_obj, file_name: str, is_training: bool) -> str:
        """Upload a file object."""
        import json as json_module
        endpoint = "training/files" if is_training else "test/files"
        # API expects multipart with 'document' (JSON metadata) and 'file' (content)
        document = json_module.dumps({"fileName": file_name})
        files = {
            "document": (None, document, "application/json"),
            "file": (file_name, file_obj),
        }
        data = self._client.http_post(
            f"/api/model-based-entities/{self.id}/{endpoint}",
            files=files,
        )
        return data["id"]

    def _save_ground_truth(self, file_id: str, spans: List[Dict]) -> None:
        """Save ground truth annotations for a file."""
        annotations = [{"start": s["start"], "end": s["end"]} for s in spans]
        self._client.http_post(
            f"/api/model-based-entities/{self.id}/test/files/{file_id}",
            data={"annotations": annotations, "markAsReviewed": True},
        )

    def list_test_files(self) -> List[Dict]:
        """
        List all test files for this entity.

        Returns:
            List of file info dicts with keys:
            - id: File ID
            - fileName: Original file name
            - status: Processing status (QueuedForAnalysis, ReadyForReview, Reviewed, etc.)
            - filePath: Path to the file
        """
        with requests.Session() as session:
            return self._client.http_get(
                f"/api/model-based-entities/{self.id}/test/files",
                session=session,
            )

    def list_training_files(self) -> List[Dict]:
        """
        List all training files for this entity.

        Returns:
            List of file info dicts with keys:
            - id: File ID
            - fileName: Original file name
            - status: Processing status
            - filePath: Path to the file
        """
        with requests.Session() as session:
            data = self._client.http_get(
                f"/api/model-based-entities/{self.id}/training/files",
                session=session,
            )
        # Training files endpoint returns paginated response
        return data.get("records", [])

    # --- Training Data ---

    def upload_training_data(
        self,
        files: List[Dict],
    ) -> List[str]:
        """
        Upload training files from text content.

        This method:
        1. Creates a temp .txt file for each entry
        2. Uploads via POST /training/files (multipart)

        Args:
            files: List of dicts with keys:
                - fileName (optional): Name for the file
                - text: The text content

        Returns:
            List of created file IDs
        """
        file_ids = []
        for i, file_data in enumerate(files):
            text = file_data["text"]
            file_name = file_data.get("fileName", f"training_file_{i}.txt")
            file_id = self._upload_text_as_file(text, file_name, is_training=True)
            file_ids.append(file_id)
        return file_ids

    def upload_training_file(self, file_path: str) -> str:
        """
        Upload a single training file from disk.

        Args:
            file_path: Path to the file (.txt, .pdf, .docx, etc.)

        Returns:
            Created file ID
        """
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            return self._upload_file(f, file_name, is_training=True)

    def upload_training_files_from_paths(
        self,
        file_paths: List[str],
    ) -> List[str]:
        """Upload multiple training files from local file paths."""
        return [self.upload_training_file(p) for p in file_paths]

    # --- Trained Models ---

    def create_trained_model(self, version_id: str) -> TrainedModel:
        """Create a new trained model from a version's guidelines."""
        data = self._client.http_post(
            f"/api/model-based-entities/{self.id}/training/models",
            data={"versionId": version_id},
        )
        return TrainedModel(self._client, self.id, data)

    def get_trained_model(self, model_id: str) -> TrainedModel:
        """Get a trained model by ID."""
        with requests.Session() as session:
            data = self._client.http_get(
                f"/api/model-based-entities/{self.id}/training/models/{model_id}",
                session=session,
            )
        return TrainedModel(self._client, self.id, data)

    def list_trained_models(self) -> List[TrainedModel]:
        """List all trained models for this entity."""
        with requests.Session() as session:
            data = self._client.http_get(
                f"/api/model-based-entities/{self.id}/training/models",
                session=session,
            )
        return [TrainedModel(self._client, self.id, m) for m in data]

    def get_active_model(self) -> Optional[TrainedModel]:
        """Get the currently active trained model."""
        models = self.list_trained_models()
        for model in models:
            if model.is_active:
                return model
        return None

    # --- Dataset Activation ---

    def activate_for_dataset(self, dataset_id: str) -> None:
        """Enable this entity for a dataset."""
        self._client.http_post(
            f"/api/model-based-entities/{self.id}/datasets/{dataset_id}"
        )

    def deactivate_for_dataset(self, dataset_id: str) -> None:
        """Disable this entity for a dataset."""
        self._client.http_delete(
            f"/api/model-based-entities/{self.id}/datasets/{dataset_id}"
        )
