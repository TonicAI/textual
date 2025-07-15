import json
import os
from time import sleep
from typing import Dict, List, Optional

import requests

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.audio.redacted_transcription_result import RedactedTranscriptionResult

from tonic_textual.classes.tonic_exception import (
    AudioTranscriptionResultAlreadyRetrieved,
    FileNotReadyForDownload,
)
from tonic_textual.classes.audio.redact_audio_responses import (
    TranscriptionResult
)
from tonic_textual.enums.pii_state import PiiState
from tonic_textual.redact_api import TextualNer
from tonic_textual.helpers.json_conversation_helper import JsonConversationHelper


class TextualAudio:
    """Wrapper class to invoke the Tonic Textual API for audio file processing

    Parameters
    ----------
    base_url : str
        The URL to your Tonic Textual instance. Do not include trailing backslashes. The default value is https://textual.tonic.ai.
    api_key : str
        Optional. Your API token. Instead of providing the API token
        here, we recommended that you set the API key in your environment as the
        value of TONIC_TEXTUAL_API_KEY.
    verify: bool
        Whether to verify SSL certification. By default, this is enabled.
    Examples
    --------
    >>> from tonic_textual.audio_api import TextualAudio
    >>> textual = TextualAudio()
    """

    def __init__(
        self,
        base_url: str = "https://textual.tonic.ai",
        api_key: Optional[str] = None,
        verify: bool = True,
    ):
        if api_key is None:
            api_key = os.environ.get("TONIC_TEXTUAL_API_KEY")
            if api_key is None:
                raise Exception(
                    "No API key provided. Either provide an API key, or set the API "
                    "key as the value of the TONIC_TEXTUAL_API_KEY environment "
                    "variable."
                )

        self.api_key = api_key
        self.client = HttpClient(base_url, self.api_key, verify)
        self.verify = verify
        self.ner = TextualNer(base_url, api_key, verify)

    def redact_audio_transcript(
        self,
        transcription: TranscriptionResult,
        generator_default: PiiState = PiiState.Redaction,
        generator_config: Dict[str, PiiState] = dict(),
        generator_metadata: Dict[str, BaseMetadata] = dict(),
        random_seed: Optional[int] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        custom_entities: Optional[List[str]] = None
    ) -> RedactedTranscriptionResult:
        """Redacts the transcription from the provided audio file.  Supports m4a, mp3, webm, mpga, wav.  Limited to 25MB or less per API call.

        Parameters
        ----------
        transcription : TranscriptionResult
            A transcription result, typically obtained by calling get_audio_transcription first.

        generator_default: PiiState = PiiState.Redaction
            The default redaction used for types that are not specified in
            generator_config. Value must be one of "Redaction", "Synthesis", or
            "Off".

        generator_config: Dict[str, PiiState]
            A dictionary of sensitive data entities. For each entity, indicates
            whether to redact, synthesize, or ignore it. Values must be one of
            "Redaction", "Synthesis", or "Off".

        generator_metadata: Dict[str, BaseMetadata]
            A dictionary of sensitive data entities. For each entity, indicates
            generator configuration in case synthesis is selected.  Values must
            be of types appropriate to the PII type.

        random_seed: Optional[int] = None
            An optional value to use to override Textual's default random
            number seeding. Can be used to ensure that different API calls use
            the same or different random seeds.

        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, ignored values). When a value for an
            entity type matches a listed regular expression, the value is
            ignored and is not redacted or synthesized.

        custom_entities: Optional[List[str]]
            A list of custom entity type identifiers to include. Each custom
            entity type included here may also be included in the generator
            config. Custom entity types will respect generator defaults if they
            are not specified in the generator config.
                        
        Returns
        -------
        RedactedTranscriptionResult
            The redacted transcription

        Examples
        --------
            >>> textual.redact_audio(
            >>>     <path to file>,
            >>>     # only redacts NAME_GIVEN
            >>>     generator_default="Off",
            >>>     generator_config={"NAME_GIVEN": "Redaction"},
            >>>     random_seed = 123,
            >>>     # Occurrences of "There" are treated as NAME_GIVEN entities
            >>>     label_allow_lists={"NAME_GIVEN": ["There"]},
            >>>     # Text matching the regex ` ([a-z]{2}) ` is not treated as an occurrence of NAME_FAMILY
            >>>     label_block_lists={"NAME_FAMILY": [" ([a-z]{2}) "]},
            >>>     # The custom entities passed here will be included in the redaction and may be included in generator_config
            >>>     custom_entities=["CUSTOM_COGNITIVE_ACCESS_KEY", "CUSTOM_PERSONAL_GRAVITY_INDEX"],
            >>> )
        """

        helper = JsonConversationHelper()

        def redact(content: str):
            return self.ner.redact(
                content,
                generator_config=generator_config,
                generator_default=generator_default,
                generator_metadata=generator_metadata,
                label_block_lists=label_block_lists,
                random_seed=random_seed,
                custom_entities=custom_entities
            )

        join_char = '\n'
        redactions = helper.redact(transcription, lambda x: x["segments"], lambda x: x["text"], lambda content: redact(content), join_char=join_char)
        full_text = join_char.join([r.redacted_text for r in redactions])

        return RedactedTranscriptionResult(transcription, full_text, redactions, redactions)

    def get_audio_transcript(
        self,
        file_path: str,            
        num_retries: Optional[int] = 30,
        wait_between_retries: Optional[int] = 10,
    ) -> TranscriptionResult:
        """Redacts the transcription from the provided audio file.  Supports m4a, mp3, webm, mpga, wav.  Limited to 25MB or less per API call.

        Parameters
        ----------
        file_path : str
            The path to the audio file.

        num_retries: Optional[int] = 30
            Defaults to 30. An optional value to specify the number of times to attempt to
            fetch the result. If a file is not yet ready for download, Textual
            pauses for 10 seconds before each retrying.

        wait_between_retries: int = 10
            The number of seconds to wait between retry attempts. (The default
            value is 10)
                        
        Returns
        -------
        TranscriptionResult : dict
            The transcription of the audio file
        """

    
        with open(file_path,'rb') as file:
            files = {
                "document": (
                    None,
                    json.dumps({
                        "fileName": os.path.basename(file_path),
                        "datasetId": "",
                        "csvConfig": {},
                        "customPiiEntityIds": []

                    }),
                    "application/json",
                ),
                "file": file,
            }
            start_response = self.client.http_post("/api/audio/transcribe/start", files=files)
        
        job_id = start_response["jobId"]
        
        retries = 1
        transcription_result = None
        while retries <= num_retries:
            try:
                with requests.Session() as session:
                    transcription_result = self.client.http_get(
                        f"/api/audio/{job_id}/transcribe/result",
                        session=session
                    )
                    break
            except requests.exceptions.HTTPError as err:
                if err.response.status_code == 409:
                    retries = retries + 1
                    if retries <= num_retries:
                        sleep(wait_between_retries)
                elif err.response.status_code == 410:
                    raise AudioTranscriptionResultAlreadyRetrieved("The transcription result has already been retrieved and or was automatically deleted which happens after 5 minutes.")                
                else:
                    raise err

        if transcription_result is None:
            retryWord = "retry" if num_retries == 1 else "retries"
            raise FileNotReadyForDownload(
                f"After {num_retries} {retryWord}, the file is not yet ready to download. "
                "This is likely due to a high service load. Try again later."
            )
        
        return TranscriptionResult.from_dict(transcription_result)
    
    def redact_audio_file(
        self,
        audio_file_path: str,
        output_file_path: str,
        generator_default: PiiState = PiiState.Redaction,
        generator_config: Dict[str, PiiState] = dict(),
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
        custom_entities: Optional[List[str]] = None,
        before_beep_buffer: float = 250.0,
        after_beep_buffer: float = 250.0
    ):
        """Generates a redacted audio file by identifying and removing sensitive audio segments. Note that calling this method requires that pydub be installed in addition to the tonic_textual library.  Additionally, you'll need to ensure that your install of ffmpeg has the necessary codec support for your file type.

        Parameters
        ----------
        audio_file_path : str
            The path to the input audio file.
            Supported file types are wav, mp3, ogg, flv, wma, aac, and others. See
            https://github.com/jiaaro/pydub for complete information on file types
            supported.

        output_file_path : str
            The path to save the redacted output file. The output file path specifies
            the audio file type that the output is written as via it's extension.
            Supported file types are wav, mp3, ogg, flv, wma, and aac. See
            https://github.com/jiaaro/pydub for complete information on file types
            supported.
        
        generator_default: PiiState = PiiState.Redaction
            The default redaction used for types that are not specified in
            generator_config. Value must be one of "Redaction", "Synthesis", or
            "Off".
            
        generator_config: Dict[str, PiiState]
            A dictionary of sensitive data entities. For each entity, indicates
            whether to redact, synthesize, or ignore it. Values must be one of
            "Redaction", "Synthesis", or "Off".

        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, ignored values). When a value for an
            entity type matches a listed regular expression, the value is
            ignored and is not redacted or synthesized.

        label_allow_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, additional values). When a piece of
            text matches a listed regular expression, the text is marked as the
            entity type and is included in the redaction or synthesis.

        custom_entities: Optional[List[str]]
            A list of custom entity type identifiers to include. Each custom
            entity type included here may also be included in the generator
            config. Custom entity types will respect generator defaults if they
            are not specified in the generator config.

        before_beep_buffer : float, optional
            Buffer time (in milliseconds) to include before redaction interval
            (default is 250.0).

        after_beep_buffer : float, optional
            Buffer time (in milliseconds) to include after redaction interval
            (default is 250.0).

        Returns
        -------
        str
            The path to the redacted output audio file.
        """
        try:
            from pydub import AudioSegment
            from tonic_textual.helpers.redact_audio_file_helper import (
                get_intervals_to_redact,
                redact_audio_segment
            )
        except ImportError as _:
            raise ImportError(
                "The pydub Python package is required to redact audio files. To use this method install it via pip install pydub."
            )

        transcription = self.get_audio_transcript(audio_file_path)
        de_id_res = self.ner.redact(
            transcription.text,
            generator_default=generator_default,
            generator_config=generator_config,
            generator_metadata=dict(),
            random_seed=None,
            label_block_lists=label_block_lists,
            label_allow_lists=label_allow_lists,
            custom_entities=custom_entities
        ).de_identify_results
        intervals_to_redact = get_intervals_to_redact(
            transcription.text,
            transcription.segments,
            de_id_res
        )
        audio = AudioSegment.from_file(audio_file_path)
        redacted_audio = redact_audio_segment(
            audio,
            intervals_to_redact,
            before_beep_buffer,
            after_beep_buffer
        )

        export_format = output_file_path.split(".")[-1]
        redacted_audio.export(output_file_path, format=export_format)

        return output_file_path