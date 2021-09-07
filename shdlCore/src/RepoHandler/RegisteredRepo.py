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

registered_repo_name = tuple(cls.repo_name.lower()
                             for cls in registered_repo_list)
