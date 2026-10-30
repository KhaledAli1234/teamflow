from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory storage: correct for a single worker only.
# For multiple workers, use Limiter(key_func=get_remote_address, storage_uri="redis://...").
limiter = Limiter(key_func=get_remote_address)