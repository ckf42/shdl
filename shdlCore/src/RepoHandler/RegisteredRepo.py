from .ArxivRepoHandler import ArxivRepoHandler
from .DOIRepoHandler import DOIRepoHandler
from .JSTORRepoHandler import JSTORRepoHandler
from .SciDirRepoHandler import SciDirRepoHandler
from .IEEERepoHandler import IEEERepoHandler
from .PMIDRepoHandler import PMIDRepoHandler

registered_repo_list = [
    DOIRepoHandler,
    ArxivRepoHandler,
    JSTORRepoHandler,
    SciDirRepoHandler,
    IEEERepoHandler,
    PMIDRepoHandler
]
