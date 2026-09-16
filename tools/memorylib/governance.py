"""Current governed Builder identities shared by Memory projections."""
from __future__ import annotations


# This is an explicit governance roster, not a prediction of future Builders.
BUILDER_NUMBERS = (1, 2, 3, 4, 5)
BUILDER_NUMBER_SET = frozenset(BUILDER_NUMBERS)

BUILDER_ROLES = {
    1: "Research / Shadow / Evidence Lifecycle",
    2: "Independent Qualification / Authority",
    3: "Memory / Context / Observability",
    4: "Provider Cascade / Controlled Shadow Infrastructure",
    5: "Autonomous Development / Night Shift Dispatcher Owner",
}

# These relationships are visibility contracts, not execution authority.  They
# live beside the roster so the auditor can detect drift between consumers.
BUILDER_PROFILE_PARTNERS = {
    1: (2, 4),
    2: (4,),
    3: (),
    4: (1, 2),
    5: (1, 2, 3, 4),
}
CEO_PROFILE_PARTNERS = BUILDER_NUMBERS
