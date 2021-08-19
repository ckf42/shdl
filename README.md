# shdl

A script to fetch file by their identifiers

## Features

* Fetch document with DOI
* Custom proxy
* Custom mirrors
* Decide file name automatically

## Install

TODO: add install here

## Usage

### Document fetching

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

### Custom mirror sites

Will always use HTTPS if not specified

`shdl 10.1109/5.771073 --mirror custom.mirror.site`

(equivalent to `shdl 10.1109/5.771073 --mirror https://custom.mirror.site`)

`shdl 10.1109/5.771073 --mirror first.mirror.to.try --mirror second.mirror.to.try`

### Custom proxy

`shdl 10.1109/5.771073 --proxy socks5h://127.0.0.1:9150`

### Filename control

`shdl 10.1109/5.771073` → `paskin1999.pdf`

`shdl 10.1109/5.771073 --output topsecret` → `topsecret.pdf`

`shdl 10.1109/5.771073 --autoname` → `[N. Paskin, doi 10.1109 5.771073]Toward Unique Identifiers.pdf`

## Dependencies

* Python 3 (tested on 3.8+)
* [requests[socks]](https://pypi.org/project/requests/ "PyPI") (tested on 2.26.0)

## TODO

* Features
    * Support for arXiv
    * Support for PMID
    * Direct search with e.g. Google Scholar?
* Usability
    * check network connectivity when no proxy is configured
    * Provide module integration
    * Export as (cross-platform) executable
    * Optimize dependencies
        * Use urllib instead of requests?
* Testing
    * Test on other versions of Python
    * Check compatibility on other OS
* Miscellaneous
    * Better repo structure organization

## License

MIT
