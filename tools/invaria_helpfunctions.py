# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy",
#   "pypdf",
# ]
# ///

# TODO: Fill Constant info symbol from e.g. PDF
# TODO: Extract ConstantCategory info from e.g. PDF
# TODO: Use unit library (e.g. unify or zero) in Constant unit field (also see README.md)


import dataclasses
import enum
from pypdf import PdfReader
import pathlib


class ConstantCategory(enum.StrEnum):
    """Valid categories."""

    UNIVERSAL = "UNIVERSAL"
    ELECTROMAGNETIC = "ELECTROMAGNETIC"
    ATOMIC_AND_NUCLEAR = "ATOMIC AND NUCLEAR"
    PHYSICOCHEMICAL = "PHYSICOCHEMICAL"


class AtomicNuclearSubcategory(enum.StrEnum):
    """Valid subcategories of ConstantCategory.ATOMIC_AND_NUCLEAR"""

    GENERAL = "General"
    ELECTROWEAK = "Electroweak"
    ELECTRON = "Electron, e−"
    MUON = "Muon, μ−"
    TAU = "Tau, τ−"
    PROTON = "Proton, p"
    NEUTRON = "Neutron, n"
    DEUTERON = "Deuteron, d"
    TRITON = "Triton, t"
    HELION = "Helion, h"
    ALPHA_PARTICLE = "Alpha particle, α"


@dataclasses.dataclass
class Constant:
    """A physical constant with uncertainty, unit, description, ..."""

    quantity: str
    symbol: str | None
    value: float | int
    uncertainty: float | None
    unit: str | None
    category: ConstantCategory | None = None


class TypstUnitLib(enum.StrEnum):
    """Typst libraries that can handle units and are implemented in this package."""

    UNIFY = enum.auto()
    ZERO = enum.auto()


def read_nist_ascii(
    nist_ascii_file: pathlib.Path, col_names_line: int = 10, start_data: int = 12
) -> list[Constant]:
    def parse_value(num: str) -> int | float:
        """Parses a string number and converts it to an integer or float."""
        if "." in num or "e" in num:
            return float(num.replace(" ", "").replace("...", ""))

        return int(num.replace(" ", ""))

    def parse_uncertainty(unc: str) -> int | float | None:
        """Parses a string uncertainty and converts it to a None value or float."""
        if "exact" in unc:
            return None

        return parse_value(unc)

    def parse_unit(unit: str, typst_pkg: TypstUnitLib = TypstUnitLib.UNIFY) -> str:
        """Parses a string unit and converts it to a typst unit."""
        # TODO: implement
        return unit

    if start_data <= col_names_line:
        raise ValueError("The column names should be above the data.")

    colnames = None
    data: list[Constant] = []
    with open(nist_ascii_file, "r") as f:
        for i, line in enumerate(f):
            if i == col_names_line - 1:
                colnames = line.split()
                continue
            if i < start_data - 1:
                continue

            if colnames is None:
                raise RuntimeError(
                    "The colnames variable should already be read and set."
                )

            line_vals = [c for c in line.strip().split("  ") if c]

            data.append(
                Constant(
                    quantity=line_vals[0],
                    symbol=None,
                    value=parse_value(line_vals[1]),
                    uncertainty=parse_uncertainty(line_vals[2]),
                    unit=None if len(line_vals) < 4 else parse_unit(line_vals[3]),
                )
            )

    return data


def read_nist_pdf(
    nist_pdf_file: pathlib.Path,
) -> None:
    """Extract Constant information from the PDF.

    Reference: https://pypdf.readthedocs.io/en/stable/user/extract-text.html

    Other libraries that might succeed:
    - Pymupdf https://pymupdf.readthedocs.io/en/latest/index.html
        - PyMuPDF extension Layout
          https://pymupdf.readthedocs.io/en/latest/pymupdf-layout/index.html
    - textract https://textract.readthedocs.io/en/stable/python_package.html
    -
    """
    # TODO: Not sure how to map the PDF info to the ASCII info to also have the ConstantCategory
    #       Maybe https://stackoverflow.com/questions/10018679/python-find-closest-string-from-a-list-to-another-string helps

    reader = PdfReader(nist_pdf_file)

    parts = []

    def constants_body(text, user_matrix, tm_matrix, font_dict, font_size) -> None:
        header_above = 640.0
        footer_below = 50.0

        # quantity_column = 160.0
        # symbol_column = 240.0
        # value_column = 390.0
        # unit_column = 500.0

        y = tm_matrix[5]
        if footer_below < y < header_above:
            parts.append(text)

    for page in reader.pages[:2]:
        page.extract_text(visitor_text=constants_body)

    text_body = "".join(parts)

    print(text_body)

    data = []
    current_const_category: ConstantCategory | None = None
    current_atomic_nuclear_subcategory: AtomicNuclearSubcategory | None = None
    for line in text_body.splitlines():
        line = line.strip()
        if line in [cat.value for cat in ConstantCategory]:
            current_const_category = ConstantCategory(line)
            continue
        if (
            current_const_category is ConstantCategory.ATOMIC_AND_NUCLEAR
            and line.strip() in [sub_cat.value for sub_cat in AtomicNuclearSubcategory]
        ):
            current_atomic_nuclear_subcategory = AtomicNuclearSubcategory(line)
            continue

        line_vals = [c for c in line.strip().split("  ") if c]


def constants2typst(constants: list[Constant], ofolder: pathlib.Path) -> None:
    """Write the list of constants to a typst file."""

    def convert_none(val: None | str | int | float) -> str | int | float:
        """Convert values that might be python None to typst none."""
        if val is None:
            return "none"
        return val

    typst_file_header = """
// This file was autogenerated. Please refer to the project README for instructions.

#import "../common_packages.typ": *

"""

    category_groups: dict[ConstantCategory | None, list[Constant]] = {
        cc: [] for cc in list(ConstantCategory) + [None]
    }
    for constant in constants:
        category_groups[constant.category].append(constant)

    for category, category_constants in category_groups.items():
        if len(category_constants) > 0:
            with open(
                ofolder
                / f"{'unknown' if category is None else category.name.lower()}.typ",
                "w",
            ) as of:
                _ = of.write(typst_file_header)
                for const in category_constants:
                    _ = of.write(
                        f"""#let {const.symbol} = (val: {const.value}, uncert: {convert_none(const.uncertainty)}, unit: "{convert_none(const.unit)}", quantity: "{const.quantity}")\n"""
                    )


if __name__ == "__main__":
    ascii = read_nist_ascii(pathlib.Path("data-sources/CODATA2022/allascii.txt"))
    print(ascii)
    # pdf = read_nist_pdf(pathlib.Path("data-sources/CODATA2022/all.pdf"))
    # print(pdf)

    constants2typst(ascii, ofolder=pathlib.Path("src/CODATA2022"))
