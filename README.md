# Invaria

This is a Typst package for providing (physical) constants. It is derived from the following sources:

- Fundamental Physical Constants of [NIST](http://physics.nist.gov/constants) (2022 CODATA recommended values)[^1]
  - [PDF](https://physics.nist.gov/cuu/pdf/all.pdf)
  - [Text](https://physics.nist.gov/cuu/Constants/Table/allascii.txt)
- [SciPy constants](https://docs.scipy.org/doc/scipy/reference/constants.html)


## Usage

The constants are accessible by revision.

**TODO**


## Development

The idea of this library is to use a python script to extracts the information from various data sources, structure it and output the typst files.
You can use e.g. `pipx` or `uv` to run the script: 
```shell
# pipx
pipx run tools/invaria_helpfunctions.py
# or using uv
uv run tools/invaria_helpfunctions.py
```


### Planned features

- [ ] Integration with typst packages, providing supports for typesetting numbers and units
    - [ ] [unify](https://typst.app/universe/package/unify)
    - [ ] [zero](https://typst.app/universe/package/zero)

## References
[^1]: Eite Tiesinga, Peter J. Mohr, David B. Newell, and Barry N. Taylor (2024), "The 2022 CODATA Recommended Values of the Fundamental Physical Constants" (Web Version 9.0). Database developed by J. Baker, M. Douma, and S. Kotochigova. Available at https://physics.nist.gov/constants, National Institute of Standards and Technology, Gaithersburg, MD 20899.
