from typing import TypeAlias

from pydantic import Field, RootModel

from cccrawl.crawlers.codeforces import CodeforcesIntegration
from cccrawl.crawlers.cses import CsesIntegration

IntegrationsUnionT: TypeAlias = CodeforcesIntegration | CsesIntegration


class AnyIntegration(RootModel):
    root: IntegrationsUnionT = Field(..., discriminator="platform")
