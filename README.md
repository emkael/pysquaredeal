PySquareDeal
============

Python port of Hans van Staveren's [SquareDeal](https://github.com/hansvanstaveren/BigDeal) software to generate bridge hand records in non-repudiated way.

In contrast to the original interface, PySquareDeal allows for SQD/SQK file manipulation in a non-interactive manner.

File format and options are compatible with 2.1 version of SquareDeal, as of February 2024.

Pre-requisites
--------------

 * Python 3.x with standard modules
 * `bigdealx` binary in a known path

Configuration
-------------

Path to `bigdealx` that's used by `pysquaredeal.py` can be set in `BIGDEALX_PATH` environment variable.

The working directory for `bigdealx` is the directory of SQD/SQK files. This means you can have your `.bigdealrc` file there to configure BigDeal options (i.e. formats which will get generated). If the `.bigdealrc` file is missing, PySquareDeal will temporarily create it, with PBN as an output format.

Usage
-----

```
python pysquaredeal.py [-h] [--sqk-file SQK_FILE] [--encoding ENCODING] [--bigdealx-path BIGDEALX_PATH] SQD_FILE COMMAND ...
```

Command arguments:

 * `SQD_FILE`: path to SQD file
 * `COMMAND`: one of the commands below
    - `create`: create new SQD/SQK pair
    - `set_name`: edit event name
    - `set_di`: edit event delayed information (its description ahead of time)
    - `add_phase`: add event phase
    - `publish`: mark SQD as published
    - `set_dv`: edit event delayed information (its value)
    - `generate`: generate PBN

Optional arguments:

 * `-h`, `--help`: show help message and exit
 * `--sqk-file SQK_FILE`: path to SQK file, if not provided, deduced from SQD file
 * `--encoding ENCODING`: SQD/SQK input file encoding, defaults to UTF-8, output is always UTF-8
 * `--bigdealx-path BIGDEALX_PATH`: path to `bigdealx` executable, overrides BIGDEALX_PATH environment variable if set

Command-specific options:

```
python pysquaredeal.py SQD_FILE create [--event-name EVENT_NAME] [--delayed-information DELAYED_INFO] [--overwrite]
```

 * `--event-name EVENT_NAME`: event name (description), optional
 * `--delayed-information DELAYED_INFO`: (description of) delayed information, optional
 * `--overwrite`: overwrite output file if exists, otherwise error is raised

```
python pysquaredeal.py SQD_FILE set_name EVENT_NAME
```

 * `EVENT_NAME`: event name (description)

```
python pysquaredeal.py SQD_FILE set_di DELAYED_INFO
```

 * `DELAYED_INFO`: description of delayed information

```
python pysquaredeal.py SQD_FILE add_phase NO_SESSIONS NO_BOARDS PREFIX [DESCRIPTION]
```

 * `NO_SESSIONS`: number of sessions in phase
 * `NO_BOARDS`: number of boards in each session, also accepts syntax like `1-10,11-20,21-30`, or `3x7` (equivalent to `1-7,8-14,15-21`)
 * `PREFIX`: output file prefix (`#` will be replaced by session number, count of `#` characters translates to number of digits, so `##` produces `01`, `02` etc.)
 * `DESCRIPTION`: phase description, optional

```
python pysquaredeal.py SQD_FILE publish
```

This one's got no options.

```
python pysquaredeal.py SQD_FILE set_dv DELAYED_INFO
```

 * `DELAYED_INFO`: value of delayed information

```
python pysquaredeal.py SQD_FILE generate [--reserve] [PHASE] [SESSION]
```

positional arguments:
 * `PHASE`: phase number or range, if empty, all phases will be generated
 * `SESSION`: session number or range, if empty, all sessions will be generated
 * `--reserve`: generate reserve board set, optional

Authors
-------

Python port written by Michał Klichowicz (mkl).

BigDeal, BigDealX and SquareDeal created by Hans van Staveren.

License
-------

[Simplified BSD license](LICENSE)

---

`Same as it ever was.`
