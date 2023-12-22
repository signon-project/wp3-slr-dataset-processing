# Sign language recognition dataset processing

This repository contains the code used to create machine learning ready datasets from the sign language video corpora for:

- Flemish sign language (VGT): `vgt/`
- Sign language of the Netherlands (NGT): `ngt/`
- British sign language (BSL): `bsl/`
- Irish sign language (ISL): `isl/`
- Spanish sign language (LSE): `lse/`

These corpora have a similar format (EAF files and video files), but their own peculiarities and annotation standards. Therefore, the main structure is similar for every repository but the implementation details differ.
For more details, please refer to the README files for the individual languages.

The repository also contains the code that was used to perform the SLR processing for the [BeCoS corpus](https://clinjournal.org/clinj/article/view/144), including language identification and keypoint extraction.

- `vgt_covid_be/`

# Usage

1. Create a virtual environment `python3 -m venv .env`
2. Activate it `source .env/bin/activate`
3. Install the required packages `pip install -r requirements.txt`
4. Run the code as details in the READMEs per language folder

# LICENSE

This code is licensed under the Apache License, Version 2.0 (LICENSE or http://www.apache.org/licenses/LICENSE-2.0).
