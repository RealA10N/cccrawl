from typing import TypeAlias

from pydantic import Field, RootModel

from cccrawl.integrations.codeforces import CodeforcesIntegration
from cccrawl.integrations.cses import CsesIntegration

IntegrationsUnionT: TypeAlias = CodeforcesIntegration | CsesIntegration


class AnyIntegration(RootModel):
    root: IntegrationsUnionT = Field(..., discriminator="platform")
