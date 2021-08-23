from ArxivRepoHandler import *
from CommonUtil import *

if __name__ != '__main__':
    quit()

print(cliArg)

registered_repo_cls = [ArxivRepoHandler, ]

query_type_cls = next((cls
                       for cls in registered_repo_cls
                       if cls.is_query_valid(cliArg.doi)), None)
if query_type_cls is None:
    error_reporter.quit_now(ErrorType.QUERY_INVALID)
else:
    verbose_print(f"Detected repo: {query_type_cls.get_repo_name()}")