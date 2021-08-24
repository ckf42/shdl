# register repo handler here

from src.RepoHandler.ArxivRepoHandler import ArxivRepoHandler
from src.RepoHandler.DOIRepoHandler import DOIRepoHandler

# query are checked in this order
registered_repo_list = [ArxivRepoHandler, DOIRepoHandler]