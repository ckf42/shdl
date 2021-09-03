# shdl

A simple utility to fetch remote files by their identifiers

## Features

* Fetch documents by their identifiers from online mirrors
* Custom proxy
* Custom mirrors
* Decide file name via its metadata

## Install

To use the script, you will need:

* Python 3.8+
* [requests package](https://pypi.org/project/requests/ "PyPI page")
* [PySocks package](https://pypi.org/project/PySocks/ "PyPI page")

To use this script, you need to first install Python 3.8+, then

* clone this repo and install all dependencies via `pip install --user -r requirements.txt`; or
* install the pre-built wheel from [release page](https://github.com/ckf42/shdl/releases)
  with `pip --user install shdl.whl`
* install the pre-built wheel with `pipx install shdl.whl --include-deps`

You can build the wheel yourself with `python -m build` (You may need `pip install -U build` first)

Alternatively, you can use [the standalone executable](https://github.com/ckf42/shdl/releases). It is (currently)
only available for Windows x64 and is considered experimental. **Use at your own risk**.

To build the standalone executable, install [PyInstaller](https://www.pyinstaller.org/) (and optionally [UPX](https://upx.github.io/)), then execute `pyinstaller --onefile --icon NONE shdl.py`.

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

### Different DOI query formats

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
* `authors80`: same as `authors`, but when cut off when the string is more than 80 characters. `et al` is added if there
  are names omitted
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

Double quotes are required if the format string contains space.

The key `year` (and `year2`) may not be available in metadata. In this case, they will be replaced by an empty string.

Note that the file extension is always untouched.

### arXiv support

`shdl "arxiv: 1501.00001"`

`shdl https://arxiv.org/abs/1501.00001`

### JSTOR supprt

*Experimental*

`shdl "jstor: 26494158"`

`shdl https://www.jstor.org/stable/26494158`

### ScienceDirect support

*Experimental*

`shdl "scidir: S0273117721000740"`

`shdl https://www.sciencedirect.com/science/article/pii/S0273117721000740`

If the target document has a DOI, `shdl` will always use it for file fetching.

### IEEE support

*Experimental*

`shdl "ieee: 1710233"`

`shdl https://ieeexplore.ieee.org/document/1710233`

If the target document has a DOI, `shdl` will always use it for file fetching.

## Config file

You can store your default configurations for `shdl` in a UTF-8 encoded text file.

By default, `shdl` will look for `.shdlconfig` at home directory `~` (Windows: `%USERPROFILE%`). You can also specify
the path to this file with `--config`. To stop looking for `.shdlconfig` file, or simply put an empty string in the
commandline option (`--config ""`)

If this file exists (and can be read), it will be parsed line by line as follows:

* Lines that start with one of these keywords (`proxy`, `mirror`, `dir`, `chunk`, `useragent`, `autoname`
  , `autoformat`, `nocolor`, case-insensitive) followed by an equal sign `=` are parsed
    * The remaining portion of the line is taken as parameter.
    * If these keywords `proxy`, `dir`, `useragent`, `chunk`, `autoformat` are specified more than once, only the last
      one is used.
    * If the keyword is `autoname`, `--autoname` will be set (as `True`), ignoring the parameter. Similar for `nocolor`
    * `mirror` can be specified multiple times for multiple mirrors.
* All other lines are ignored.

Entries in `.shdlconfig` have lower priority than commandline arguments, meaning that the corresponding commandline
arguments will **override** the settings in `.shdlconfig`, including `mirror`.

**NOTE** This feature is experimental and is subject to change.

### Example

Putting the following content in `.shdlconfig`

```text
proxy=socks5h://127.0.0.1:9050
this line will be ignored
this=line=will=also=be=ignored
mirror=first.mirror
dir=./this_will_not_be_used
nocolor=this message will be ignored
dir=~/document directory to save file
mirror=second.mirror
autoname=these words will be ignored
```

is the same as
specifying `--proxy socks5h://127.0.0.1:9050 --mirror first.mirror --nocolor --dir "~/document directory to save file" --mirror second.mirror --autoname`
when calling `shdl`

Note that argument for `--dir` is `"~/document directory to save file"`

## Dependencies

Listing only the explicit ones

* Python 3 (support 3.8, 3.9)
* [requests](https://pypi.org/project/requests/ "PyPI page") ~= 2.26.0 (Apache 2.0)
* [PySocks](https://pypi.org/project/PySocks/ "PyPI page") ~= 1.7.1 (BSD-3)

## TODO

### Features

* Support for PMID
* Direct search with e.g. Google Scholar?
* Better `--autoformat` syntax for flexibility?

### Usability

* Check if build specs are alright
* Check why PyInstaller sometimes packs hooks that are not needed (e.g. IPython, matplotlib) and bloats size to ~16MB

### Design

* Optimize dependencies
    * Use urllib instead of requests?

### Testing

* Test on other versions of Python
* Check compatibility on other OS
* Better tests

### Miscellaneous

* Check if MIT is an appropriate license

## License

MIT
