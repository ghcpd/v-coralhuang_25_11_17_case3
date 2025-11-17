"""Shared Flask extensions for the fixed module."""

from flask_sqlalchemy import SQLAlchemy

# Lazy extension: real connections are created when an app initializes it.
db = SQLAlchemy(session_options={"autoflush": False, "expire_on_commit": False})

