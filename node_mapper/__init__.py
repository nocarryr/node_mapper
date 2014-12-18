import os
import site

site.addsitedir(os.path.dirname(__file__))
print os.path.dirname(__file__)
