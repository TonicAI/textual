<a id="readme-top"></a>

<p align="center">
    <a href="https://www.python.org/">
            <img alt="Build" src="https://img.shields.io/badge/Made%20with-Python-1f425f.svg?color=purple">
    </a>
    <a href="https://github.com/tonicai/textual_sdk_internal/blob/master/LICENSE">
        <img alt="License" src="https://img.shields.io/badge/license-MIT-blue">
    </a>
    <a href='https://tonic-ai-textual-sdk.readthedocs-hosted.com/en/latest/?badge=latest'>
      <img src='https://readthedocs.com/projects/tonic-ai-textual-sdk/badge/?version=latest' alt='Documentation Status' />
    </a>
</p>


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/tonicai/textual_sdk">
    <img src="images/tonic-textual.svg" alt="Logo" width="80" height="80">
  </a>
  <h1 align="center">Tonic Textual</h1>

<h3 align="center">Tonic Textual SDK for Python</h3>
  <p align="center">
     <p>AI-ready data, with privacy at the core. Unblock AI initiatives by maximizing your free-text assets through realistic data de-identification and high quality data extraction</p>
</p>
    <br />
    <a href="https://tonic-ai-textual-sdk.readthedocs-hosted.com/en/latest/"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://textual.tonic.ai/signup">Get an API Key</a>
    ·
    <a href="https://github.com/tonicai/textual_sdk/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/tonicai/textual_sdk/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->

## Table of Contents
<ol>
  <li>
    <a href="#getting-started">Getting Started</a>
    <ul>
      <li><a href="#prerequisites">Prerequisites</a></li>
      <li><a href="#installation">Installation</a></li>
    </ul>
  </li>
  <li>
    <a href="#usage">Usage</a>
    <ul>
      <li><a href="#ner_usage">NER Usage</a></li>
      <li><a href="#parse_usage">Parse Usage</a></li>
      <li><a href="#ui_automation">UI Automation</a></li>
    </ul>
  </li>
  <li><a href="#roadmap">Bug Reports and Feature Requests</a></li>
  <li><a href="#contributing">Contributing</a></li>
  <li><a href="#license">License</a></li>
  <li><a href="#contact">Contact</a></li>
</ol>



<!-- GETTING STARTED -->
## Prerequisites

1. Get a free API Key at [Textual](https://textual.tonic.ai)
2. Install the package from PyPI
   ```sh
   pip install tonic-textual
   ```
3. Your API Key can be passed as an argument directly into SDK calls or you can save it to your environment
   ```sh
   export TONIC_TEXTUAL_API_KEY=<API Key>
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Getting Started

This library supports two different workflows, NER detection (along with entity tokenization and synthesis) and data extraction of unstructured files like PDF and Office documents (docx, xlsx).

Each workflow, has its own respective client.  Each client, supports the same set of constructor arguments.

```
from tonic_textual.redact_api import TextualNer
from tonic_textual.parse_api import TextualParse

textual_ner = TextualNer()
textual_parse = TextualParse()
```

Both clients support the following optional arguments

1. base_url - The URL of the server, hosting Tonic Textual.  Defaults to https://textual.tonic.ai

2. api_key - Your API key.  If not specified you must set the TONIC_TEXTUAL_API_KEY in your environment

3. verify - Whether SSL Certification verification is performed.  Default is enabled.



<!-- USAGE -->
<!-- NER USAGE -->
## NER Usage

Textual can identify entities within free text.  It works on both raw text and on content found within files such as pdf, docx, xlsx, images, txt, and csv files.  For raw text, 

### Free text

```python
raw_redaction = textual_ner.redact("My name is John and I live in Atlanta.")
```

The ```raw_redaction``` returns a response like the following:

```json
{
    "original_text": "My name is John and I a live in Atlanta.",
    "redacted_text": "My name is [NAME_GIVEN_dySb5] and I a live in [LOCATION_CITY_FgBgz8WW].",
    "usage": 9,
    "de_identify_results": [
        {
            "start": 11,
            "end": 15,
            "new_start": 11,
            "new_end": 29,
            "label": "NAME_GIVEN",
            "text": "John",
            "score": 0.9,
            "language": "en",
            "new_text": "[NAME_GIVEN_dySb5]"
        },
        {
            "start": 32,
            "end": 39,
            "new_start": 46,
            "new_end": 70,
            "label": "LOCATION_CITY",
            "text": "Atlanta",
            "score": 0.9,
            "language": "en",
            "new_text": "[LOCATION_CITY_FgBgz8WW]"
        }
    ]
}
```

The ```redacted_text``` property provides the new text, with identified entities replaced with tokenized values.  Each identified entity will be listed in the ```de_identify_results``` array.

In addition to tokenizing entities, they can also be synthesized.  To synthesize specific entities use the optional ```generator_config``` argument.

```python
raw_redaction = textual_ner.redact("My name is John and I live in Atlanta.", generator_config={'LOCATION_CITY':'Synthesis', 'NAME_GIVEN':'Synthesis'})
```

This will generate a new ```redacted_text``` value in the response with synthetic entites.  For example, it could look like

| My name is Alfonzo and I live in Wilkinsburg.

### Files

Textual can also identify, tokenize, and synthesize text within files such as PDF and DOCX.  The result is a new file with specified entities either tokenized or synthesized.  

To generate a redacted file, 

```python
with open('file.pdf','rb') as f:
  ref_id = textual_ner.start_file_redact(f, 'file.pdf')

with open('redacted_file.pdf','wb') as of:
  file_bytes = textual_ner.download_redacted_file(ref_id)
  of.write(file_bytes)
```

The ```download_redacted_file``` takes similar arguments to the ```redact()``` method and supports a ```generator_config``` parameter to adjust which entities are tokenized and synthesized.

### Consistency

When entities are tokenized, the tokenized values we generate are unique to the original value.  A given entity will also generate to the same, unique token.  Tokens can be mapped back to their original value via the ```unredact``` function call.  

Synthetic entities are consistent.  This means, a given entity, such as 'Atlanta' will always get mapped to the same fake city.  Synthetic values can potentially collide and are not reversible.

To change the underlying mapping of both tokens and synthetic values, you can pass in the optional ```random_seed``` parameter in the ```redact()``` function call.  

_For more examples, please refer to the [Documentation](https://textual.tonic.ai/docs/index.html)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Parse Usage

Textual supports the extraction of text and other content from files.  Textual currently supports

- pdf
- png, tif, jpg
- txt, csv, tsv, and other plaintext formats
- docx, xlsx

Textual takes these unstructured files and converts them to a structured representation in JSON.  

The JSON output has file specific pieces, for example, table and KVP detection is performed on PDFs and images but all files support the following JSON properties:

```json
{
  "fileType": "<file type>",
  "content": {
    "text": "<Markdown file content>",
    "hash": "<hashed file content>",
    "entities": [   //Entry for each entity in the file
      {
        "start": <start location>,
        "end": <end location>,
        "label": "<value type>",
        "text": "<value text>",
        "score": <confidence score>
      }
    ]
  },
  "schemaVersion": <integer schema version>
}
```

PDFs and images additionally have properties for ```tables``` and ```kvps```.  DocX files have support for ```headers```, ```footers```, and ```endnotes``` and Xlsx files break content down a per-sheet basis.

For a detailed breakdown of the JSON schema for each file type please reference on documentation, [here](https://docs.tonic.ai/textual/pipelines/viewing-pipeline-results/pipeline-json-structure).


To parse a file one time, you can use our SDK.

```python
with open('invoice.pdf','rb') as f:
  parsed_file = textual_parse.parse_file(f.read(), 'invoice.pdf')
```

The parsed_file is a ```FileParseResult``` type and has various helper methods to retrieve content from the document.

- ```get_markdown(generator_config={})``` retrieves the document as markdown.  The markdown can be optionally tokenized/synthesized by passing in a list of entities to ```generator_config```

- ```get_chunks(generator_config={}, metadata_entities=[])``` chunks the files in a form suitable for vector DB ingestion.  Chunks can be tokenized/synthesized and additionally can be enriched with entity level metadata by providing a list of entities.  The entity list should be entities that are relevant to questions being asked to the RAG system.  e.g. if you are building a RAG for front line customer support reps, you might expect to include 'PRODUCT' and 'ORGANIZATION' as metadata entities.

In addition for processing files from you local system, you can reference files directly in S3.  The ```parse_s3_file``` function call behaves the same as ```parse_file``` but requires a bucket and key argument to specify your specific file in S3.  It uses boto3 to retrieve files in S3.

_For more examples, please refer to the [Documentation](https://textual.tonic.ai/docs/index.html)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## UI Automation

The Textual UI supports file redactionand parsing.  It provides an experience for users to orchestrate jobs and process files at scale.  It supports integrations with various bucket solutions like S3 as well as systems like Sharepoint and Databricks Unity Catalog volumes.  Actions such as building smart pipelines (for parsing) and Dataset collections (file redaction) can be completed via the SDK.

_For more examples, please refer to the [Documentation](https://textual.tonic.ai/docs/index.html)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- ROADMAP -->
## Bug Reports and Feature Requests

Bugs and Feature requests can be submitted via the [open issues](https://github.com/tonicai/textual_sdk/issues).  We try to be responsive here so any issues filed should expect a prompt response from the Textual team.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.


<!-- CONTACT -->
## Contact

Tonic AI - [@tonicfakedata](https://x.com/tonicfakedata) - support@tonic.ai

Project Link: [Textual](https://tonic.ai/textual)
