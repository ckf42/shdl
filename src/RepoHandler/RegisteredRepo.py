# register repo handler here

from src.RepoHandler.ArxivRepoHandler import *
from src.RepoHandler.DOIRepoHandler import *
from src.RepoHandler.JSTORRepoHandler import *
from src.RepoHandler.SciDirRepoHandler import *
from src.RepoHandler.IEEERepoHandler import *

# query are checked in this order
registered_repo_list = [DOIRepoHandler,
                        ArxivRepoHandler,
                        JSTORRepoHandler,
                        SciDirRepoHandler,
                        IEEERepoHandler]
