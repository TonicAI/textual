🔊 Audio
=============

The Textual audio functionality allows you to process audio files in different ways.  With this module you can:

- Generate a transcript
- Sanitize the transcript by synthesizing/redacting it
- Generate a redacted (beeped-out) audio file from the original recording

Before you can use these functions, read the :doc:`Getting started <../quickstart/getting_started>` guide and create an API key.

Textual audio processing supports m4a, mp3, webm, mpga, wav files. For file types like m4a you'll need to make sure your build of ffmpeg has the necessary libraries.  If you are using the Textual cloud or you are self-hosting but using the Azure AI Whisper integration then you'll have to limit your file sizes to 25MB or less.  If you are self-hosting Textual's ASR containers then there are no file size limitations.

.. toctree::
   :hidden:
   :maxdepth: 1

   generate_transcript
   redact_transcript
   generate_redacted_audio