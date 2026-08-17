import dataclasses
import enum
from typing import override

from .config_constants import CODATA_BASE_URL
from .helpfunctions import snake_case2kebab_case


class ConstantCategory(enum.StrEnum):
    """Base enum class of categories."""

    @property
    def url_name(self) -> str:
        """Most of the category links can be derived from the category name."""
        return "/cgi-bin/cuu/Category?view=html&" + self.replace(" ", "+")

    @property
    def constant_link_color(self) -> str:
        """The color of the constant links in the category page."""
        return "#3142BD"

    @property
    def typst_filename(self) -> str:
        """The filename for the Typst file of the category."""
        return f"{snake_case2kebab_case(self.name.lower())}.typ"


class BasicConstantCategory(ConstantCategory):
    """Valid basic constant categories as defined on the CODATA website and in the CODATA PDF.

    Have to be spelled as the link of the category on https://physics.nist.gov/cuu/Constants/index.html.
    Exceptions should be handled by an override of the `.url_name` property.
    """

    UNIVERSAL = "Universal"
    ELECTROMAGNETIC = "Electromagnetic"
    ATOMIC_AND_NUCLEAR = "Atomic and nuclear"
    PHYSICO_CHEMICAL = "Physico-chemical"


class SpecialConstantCategory(ConstantCategory):
    """Some additional categories defined on the CODATA website."""

    DEFINED_CONSTANTS = "Defined constants"
    NON_SI_UNITS = "Non-SI units"
    CONVERSION_FACTORS = "Conversion factors for energy equivalents"
    X_RAY_VALUES = "X-ray values"

    @property
    @override
    def url_name(self) -> str:
        """Most of the links can just be derived from the category name.

        Unfortunately the database has some exceptions…
        """
        match self:
            case SpecialConstantCategory.DEFINED_CONSTANTS:
                return "/cgi-bin/cuu/Category?view=html&Adopted+values"
            case SpecialConstantCategory.CONVERSION_FACTORS:
                return "/cuu/Constants/factorlist.html"
            case _:
                return super().url_name

    @property
    @override
    def constant_link_color(self) -> str:
        match self:
            case SpecialConstantCategory.CONVERSION_FACTORS:
                return "#a33c43"
            case _:
                return super().constant_link_color


class AtomicNuclearSubcategory(ConstantCategory):
    """Valid subcategories of ATOMIC_AND_NUCLEAR"""

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
        """Get an identifier that can be used as a Typst variable name."""
        # TODO: Could be improved performance wise
        normalized = (
            self.quantity.lower()
            .replace(" ", "_")
            .replace("/", "_per_")
            .replace(".", "")
            .replace(",", "")
            .replace("(", "")
            .replace(")", "")
            .replace("-", "")
        )

        # Convert to camel case
        return snake_case2kebab_case(normalized)

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
