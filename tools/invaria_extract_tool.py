# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy",
#   "pypdf",
# ]
# ///

import logging
import pathlib
from typing import Final

from invaria_pylib.file_writers import (
    constants2typst,
    constants2yaml,
    write_unittest_files,
)
from invaria_pylib.helpclasses import (
    BasicConstantCategory,
    Constant,
    ConstantCategory,
    SpecialConstantCategory,
)
from invaria_pylib.nist_data_readers import read_nist_ascii, scrape_nist

logging.basicConfig()


# Some constants
CODATA_BASE_URL: Final[str] = "https://physics.nist.gov"
CODATA_CATEGORY_BASE_URL: Final[str] = (
    f"{CODATA_BASE_URL}/cgi-bin/cuu/Category?view=html"
)
CODATA_CONSTANT_LATEX_IMAGE_BASE_URL = f"{CODATA_BASE_URL}/cuu/Constants/Value/gif/"


if __name__ == "__main__":
    nist_constants = read_nist_ascii(
        pathlib.Path("data-sources/CODATA2022/allascii.txt")
    )
    # nist_pdf = read_nist_pdf(pathlib.Path("data-sources/CODATA2022/all.pdf"))

    scrape_nist(nist_constants)

    nist_categorized_constants: dict[ConstantCategory | None, list[Constant]] = {
        cc: [] for cc in [*BasicConstantCategory, *SpecialConstantCategory] + [None]
    }
    for constant in nist_constants:
        if len(constant.categories) == 0:
            nist_categorized_constants[None].append(constant)
            continue
        for category in constant.categories:
            nist_categorized_constants[category].append(constant)

    constants2yaml(nist_constants, ofolder=pathlib.Path("src/CODATA2022/"))
    dataset_import_filename = constants2typst(
        nist_categorized_constants, ofolder=pathlib.Path("src/CODATA2022/")
    )

    write_unittest_files(
        categorized_constants=nist_categorized_constants,
        dataset_import_filename=dataset_import_filename,
        unittestfolder=pathlib.Path("tests/codata2022"),
    )
