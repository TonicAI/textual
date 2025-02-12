<a id="readme-top"></a>

<h1 align="center">
  <img style="vertical-align:middle" height="200" src="https://raw.githubusercontent.com/TonicAI/textual/main/images/textual-logo.png">
</h1>

<p align="center">Unblock AI initiatives by maximizing your free-text assets through realistic data de-identification and high quality data extraction 🚀</p>

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

<p align="center">
  <a href="https://tonic-textual-sdk.readthedocs-hosted.com/en/latest/">Documentation</a>
  |
  <a href="https://textual.tonic.ai/signup">Get an API key</a>
  |
  <a href="https://github.com/tonicai/textual_sdk/issues/new?labels=bug&template=bug-report---.md">Report a bug</a>
  |
  <a href="https://github.com/tonicai/textual_sdk/issues/new?labels=enhancement&template=feature-request---.md">Request a feature</a>
</p>

Textual makes it easy to build safe AI models and applications on sensitive customer data. It is used across industries, with a primary focus on finance, healthcare, and customer support. Build safe models by using Textual to identify customer PII/PHI, then generate synthetic text and documents that you can use to train your models without inadvertently embedding PII/PHI into your model weights.

Textual comes with a built-in data pipeline functionality so that it scales with you. Use our SDK to redact text or to extract relevant information from complex documents before you build your data pipelines.


## Key Features

- 🔎 NER. Our models are fast and accurate. Use them on real-world, complex, and messy unstructured data to find the exact entities that you care about.
- 🧬 Synthesis. We don't just find sensitive data. We also synthesize it, to provide you with a new version of your data that 
is suitable for model training and AI development.
- ⛏️ Extraction. We support a variety of file formats in addition to txt. We can extract interesting data from PDFs, DOCX files, images, and more.


<!-- TABLE OF CONTENTS -->

## 📚 Contents
<ol>
  <li><a href="#prerequisites">Prerequisites</a></li>
  <li><a href="#getting-started">Getting started</a></li>
  <li><a href="#ner_usage">NER usage</a></li>
  <li><a href="#parse_usage">Parse usage</a></li>
  <li><a href="#ui_automation">UI automation</a></li>
  <li><a href="#roadmap">Bug reports and feature requests</a></li>
  <li><a href="#contributing">Contributing</a></li>
  <li><a href="#license">License</a></li>
  <li><a href="#contact">Contact</a></li>
</ol>



<!-- GETTING STARTED -->
## 📦 Installation

1. Get a free API key at [Textual.](https://textual.tonic.ai).
2. Install the package from PyPI
   ```sh
   pip install tonic-textual
   ```
3. You can pass your API key as an argument directly into SDK calls, or you can save it to your environment.
   ```sh
   export TONIC_TEXTUAL_API_KEY=<API Key>
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🏃‍♂ Getting started

This library supports the following workflows:

* NER detection, along with entity tokenization and synthesis
* Data extraction of unstructured files such as PDFs and Office documents (docx, xlsx).

Each workflow has its own client. Each client supports the same set of constructor arguments.

```
from tonic_textual.redact_api import TextualNer
from tonic_textual.parse_api import TextualParse

textual_ner = TextualNer()
textual_parse = TextualParse()
```

Both clients support the following optional arguments:

- ```base_url``` - The URL of the server that hosts Tonic Textual. Defaults to https://textual.tonic.ai

- ```api_key``` - Your API key. If not specified, you must set TONIC_TEXTUAL_API_KEY in your environment.

- ```verify``` - Whether to verify SSL certification. Default is true.


## 🔎 NER usage

Textual can identify entities within free text. It works on raw text and on content from files, including pdf, docx, xlsx, images, txt, and csv files. 

### Free text

```python
raw_redaction = textual_ner.redact("My name is John and I live in Atlanta.")
```

```raw_redaction``` returns a response similar to the following:

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

The ```redacted_text``` property provides the new text. In the new text, identified entities are replaced with tokenized values. Each identified entity is listed in the ```de_identify_results``` array.

You can also choose to synthesize entities instead of tokenizing them. To synthesize specific entities, use the optional ```generator_config``` argument.

```python
raw_redaction = textual_ner.redact("My name is John and I live in Atlanta.", generator_config={'LOCATION_CITY':'Synthesis', 'NAME_GIVEN':'Synthesis'})
```

In the response, this generates a new ```redacted_text``` value that contains the synthetic entities. For example:

| My name is Alfonzo and I live in Wilkinsburg.

### Files

Textual can also identify, tokenize, and synthesize text within files such as PDF and DOCX. The result is a new file where the specified entities are either tokenized or synthesized.  

To generate a redacted file:

```python
with open('file.pdf','rb') as f:
  ref_id = textual_ner.start_file_redact(f, 'file.pdf')

with open('redacted_file.pdf','wb') as of:
  file_bytes = textual_ner.download_redacted_file(ref_id)
  of.write(file_bytes)
```

The ```download_redacted_file``` method takes similar arguments to the ```redact()``` method. It also supports a ```generator_config``` parameter to adjust which entities are tokenized and synthesized.

### Consistency

When entities are tokenized, the tokenized values are unique to the original value. A given entity always generates to the same unique token. To map a token back to its original value, use the ```unredact``` function call.  

Synthetic entities are consistent. This means that a given entity, such as 'Atlanta', is always mapped to the same fake city. Synthetic values can potentially collide and are not reversible.

To change the underlying mapping of both tokens and synthetic values, in the ```redact()``` function call, pass in the optional ```random_seed``` parameter.  

_For more examples, refer to the [Textual SDK documentation](https://textual.tonic.ai/docs/index.html)._

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## ⛏️ Parse usage

Textual supports the extraction of text and other content from files. Textual currently supports:

- pdf
- png, tif, jpg
- txt, csv, tsv, and other plaintext formats
- docx, xlsx

Textual takes these unstructured files and converts them to a structured representation in JSON.  

The JSON output has file-specific pieces. For example, table and KVP detection is only performed on PDFs and images. However, all files support the following JSON properties:

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

PDFs and images have additional properties for ```tables``` and ```kvps```.

DocX files support ```headers```, ```footers```, and ```endnotes```.

Xlsx files break down the content by the individual sheets.

For a detailed breakdown of the JSON schema for each file type, go to the [JSON schema information in the Textual guide](https://docs.tonic.ai/textual/pipelines/viewing-pipeline-results/pipeline-json-structure).


To parse a file one time, you can use our SDK.

```python
with open('invoice.pdf','rb') as f:
  parsed_file = textual_parse.parse_file(f.read(), 'invoice.pdf')
```

The parsed_file is a ```FileParseResult``` type, which has helper methods that you can use to retrieve content from the document.

- ```get_markdown(generator_config={})``` retrieves the document as Markdown. To tokenize or synthesize the Markdown, pass in a list of entities to ```generator_config```.

- ```get_chunks(generator_config={}, metadata_entities=[])``` chunks the files in a form suitable for vector database ingestion. To tokenize or synthesize chunks, or enrich them with entity level metadata, provide a list of entities. The listed entities should be relevant to the questions that are asked of the RAG system. For example, if you are building a RAG for front line customer support reps, you might expect to include 'PRODUCT' and 'ORGANIZATION' as metadata entities.

In addition to processing files from your local system, you can reference files directly from Amazon S3. The ```parse_s3_file``` function call behaves the same as ```parse_file```, but requires a bucket and key argument to specify your specific file in Amazon S3. It uses boto3 to retrieve the files from Amazon S3.

_For more examples, refer to the [Textual SDK documentation](https://textual.tonic.ai/docs/index.html)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## 💻 UI automation

The Textual UI supports file redaction and parsing. It provides an experience for users to orchestrate jobs and process files at scale. It supports integrations with various bucket solutions such as Amazon S3, as well as systems such as Sharepoint and Databricks Unity Catalog volumes.

You can use the SDK for actions such as building smart pipelines (for parsing) and dataset collections (for file redaction).

_For more examples, refer to the [Textual SDK documentation](https://textual.tonic.ai/docs/index.html)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- ROADMAP -->
## Bug reports and feature requests

To submit a bug or feature request, go to [open issues](https://github.com/tonicai/textual_sdk/issues). We try to be responsive here - any issues filed should expect a prompt response from the Textual team.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, fork the repo and create a pull request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

You can also simply open an issue with the tag "enhancement".

Don't forget to give the project a star! Thanks again!

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- LICENSE -->
## License

Distributed under the MIT License. For more information, see `LICENSE.txt`.


<!-- CONTACT -->
## Contact

Tonic AI - [@tonicfakedata](https://x.com/tonicfakedata) - support@tonic.ai

Project Link: [Textual](https://tonic.ai/textual)
