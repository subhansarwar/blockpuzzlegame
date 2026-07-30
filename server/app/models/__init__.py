# app/models/__init__.py
# Import every model module so SQLAlchemy's mapper configuration and
# Base.metadata.create_all() see the full schema regardless of import order.
from app.models.users import *  # noqa: F401,F403
from app.models.game import *  # noqa: F401,F403
from app.models.social import *  # noqa: F401,F403
from app.models.shop import *  # noqa: F401,F403
