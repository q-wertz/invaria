import dataclasses
import enum

from .config_constants import CODATA_BASE_URL


class ConstantCategory(enum.StrEnum):
    """Valid categories.

    Have to be spelled as on https://physics.nist.gov/cuu/Constants/index.html.
    """

    UNIVERSAL = "Universal"
    ELECTROMAGNETIC = "Electromagnetic"
    ATOMIC_AND_NUCLEAR = "Atomic and nuclear"
    PHYSICO_CHEMICAL = "Physico-chemical"
    DEFINED_CONSTANTS = "Defined constants"
    NON_SI_UNITS = "Non-SI units"
    X_RAY_VALUES = "X-ray values"

    @property
    def url_name(self) -> str:
        """Most of the links can just be derived from the category name.

        Unfortunately the database has some exceptions...
        """
        match self:
            case ConstantCategory.DEFINED_CONSTANTS:
                return "Adopted+values"
            case _:
                return self.replace(" ", "+")


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
    categories: set[ConstantCategory] = dataclasses.field(default_factory=set)
    codata_sub_url: str | None = None

    @property
    def codata_url(self) -> str:
        """Get the full NIST CODATA URL to the constant."""
        return f"{CODATA_BASE_URL}{self.codata_sub_url}"

    @property
    def codata_identifier(self) -> str | None:
        """Get the internal NIST CODATA identifier.

        Is e.g. used in the URL of the constant.
        """
        if self.codata_sub_url is None:
            return None

        return self.codata_sub_url.split("?")[-1]

    @property
    def typst_variable_name(self) -> str:
        """Get an identifier that can be used as a typst variable name."""
        # TODO: Could be improved performance wise
        return (
            self.quantity.lower()
            .replace(" ", "_")
            .replace("/", "_per_")
            .replace(".", "")
            .replace(",", "")
            .replace("(", "")
            .replace(")", "")
        )

    def to_yaml_dict(self) -> dict[str, str | float | int | None | list[str]]:
        """Get a representation, that can be used by PyYAML."""
        return {
            "quantity": self.quantity,
            "symbol": self.symbol,
            "value": self.value,
            "uncertainty": self.uncertainty,
            "unit": self.unit,
            "categories": [category.value for category in self.categories],
            "codata_url": self.codata_url,
        }


class TypstUnitLib(enum.StrEnum):
    """Typst libraries that can handle units and are implemented in this package."""

    UNIFY = enum.auto()
    ZERO = enum.auto()
