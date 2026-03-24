Audio
=============

The Textual audio functionality allows you to process audio files in different ways.  With this module you can:

- Generate a transcript
- Synthesize or redact sensitive values in the transcript
- Generate a redacted (beeped-out) audio file from the original recording

Before you can use these functions, read the :doc:`Getting started </index>` guide and create an API key.

Textual audio processing supports the following audio file types: m4a, mp3, webm, mpga, wav

For file types such as m4a, make sure that your build of ffmpeg has the necessary libraries.

If you use Textual Cloud, or you self-host using the Azure AI Whisper integration, then file sizes are limited to 25MB or smaller.

If you self-host using Textual's Automatic Speech Recognition (ASR) containers, then there are no limitations on file size.

.. toctree::
   :hidden:
   :maxdepth: 1

   generate_transcript
   redact_transcript
   generate_redacted_audio
   api
