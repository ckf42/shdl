# shdl

A script to fetch files by their identifiers

## Features

* Fetch document with DOI and arXiv identifier
* Custom proxy
* Custom mirrors
* Decide file name via its metadata

## Install

Only available as a python script for now. To use it, you will need to install:

* Python 3
* [requests](https://pypi.org/project/requests/ "PyPI page")
    * install with `pip install --user requests`
* [PySocks](https://pypi.org/project/PySocks/ "PyPI page")
    * if you need to use socks proxy (e.g. TOR), install this with `pip install --user PySocks`
    * alternatively install `requests` with socks extra `pip install --user requests[socks]`

Standalone executable is not yet available.

## Usage

### Document fetching

By default, identifier is assumed to be DOI

Unless `--dir` is specified, file is saved to the current working directory

`shdl 10.1109/5.771073`

Save document to home directory

`shdl 10.1109/5.771073 --dir ~`

Relative path support

`shdl 10.1109/5.771073 --dir ./documents`

`shdl 10.1109/5.771073 --dir ~/documents`

### Different DOI queries

`shdl https://doi.org/10.1109/5.771073`

`shdl doi.org/10.1109/5.771073`

`shdl dx.doi.org/10.1109/5.771073`

Query string containing space must be enquoted

`shdl "doi: 10.1109/5.771073"`

(Limited) support for Springer link. They are always parsed as DOI

``shdl https://link.springer.com/referenceworkentry/10.1007/978-3-662-49054-9_923-1``

### Custom mirror sites

Will always use HTTPS if not specified

`shdl 10.1109/5.771073 --mirror custom.mirror.site`

(equivalent to `shdl 10.1109/5.771073 --mirror https://custom.mirror.site`)

`shdl 10.1109/5.771073 --mirror first.mirror.to.try --mirror second.mirror.to.try`

### Custom proxy

`shdl 10.1109/5.771073 --proxy socks5h://127.0.0.1:9150`

### Filename control

`shdl 10.1109/5.771073` → Output file name `paskin1999.pdf`

`shdl 10.1109/5.771073 --output topsecret` → Output file name `topsecret.pdf`

`shdl 10.1109/5.771073 --autoname` → Output file name `[N. Paskin, doi 10.1109@5.771073]Toward Unique Identifiers.pdf`

Control autoname format with `--autoformat "<format string>"`

`shdl 10.1088/1751-8113/44/49/492001 --autoname --autoformat "title is {title}"` → Output file
name `title is Can Apparent Superluminal Neutrino Speeds be Explained as a Quantum Weak Measurement.pdf`

Uses the [Python string formatting syntax](https://docs.python.org/3/library/string.html#formatstrings) with keyword
arguments. Available keywords are:

* `authors`: a string of comma separated names with given names abbreviated (
  e.g. `M. V. Berry, N. Brunner, S. Popescu, P. Shukla`)
* `authorEtAl`: same as `authors`, but with only the first 3 names. Remaining names will be replaced with `et al.` (
  e.g. `M. V. Berry, N. Brunner, S. Popescu, et al.`)
* `authorFamily`: same as `authors`, but with family names only (e.g. `Berry, Brunner, Popescu, Shukla`)
* `authorFamilyCamel`: same as `authorFamily`, but no separators between the family names (
  e.g. `BerryBrunnerPopescuShukla`)
* `identifier`: the document identifier, with `/` replaced by `@` (e.g. `10.1088@1751-8113@44@49@492001`)
* `repo`: the name of file repository, in lower case (e.g. `doi`)
* `title`: the title of the document, in title casing (
  e.g. `Can Apparent Superluminal Neutrino Speeds be Explained as a Quantum Weak Measurement`)
* `title_`: same as `title`, but words are separated by a single underscore and every word is capitalized (
  e.g. `Can_Apparent_Superluminal_Neutrino_Speeds_Be_Explained_As_A_Quantum_Weak_Measurement`)
* `titleCamel`: same as `title_`, but without underscores (
  e.g. `CanApparentSuperluminalNeutrinoSpeedsBeExplainedAsAQuantumWeakMeasurement`)
* `year`: the 4-digit string of the recorded publication year (e.g. `2011`)
* `year2`: the last 2 digits of `year` (e.g. `11`)

The algorithms used for checking author names and converting title into title casing are rather simple and may not give
the desired results.

Double quotes are not necessary if the format string does not include space.

The key `year` (and `year2`) may not be available in metadata. In this case, they will be replaced by an empty string.

Note that the file extension is always untouched.

### arXiv support

`shdl "arxiv: 1501.00001"`

`shdl https://arxiv.org/abs/1501.00001`

### JSTOR supprt

Still experimental

`shdl "jstor: 26494158"`

`shdl https://www.jstor.org/stable/26494158`

## Dependencies

* Python 3 (tested on 3.8, 3.9)
* [requests](https://pypi.org/project/requests/ "PyPI page") (tested on 2.26.0)
* [PySocks](https://pypi.org/project/PySocks/ "PyPI page") (tested on 1.7.1)

## TODO

### Features

* Support for PMID
* Direct search with e.g. Google Scholar?
* Better `--autoformat` syntax for flexibility?

### Usability

* Export as (cross-platform?) standalone executable
* Provide module integration
* Optimize dependencies
    * Use urllib instead of requests?

### Testing

* Test on other versions of Python
* Check compatibility on other OS

### Miscellaneous

* Better repo structure organization

## License

MIT
