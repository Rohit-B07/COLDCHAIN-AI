"""Database seeding: default roles, permissions catalog and initial admin user.

Run with ``python -m app.seed``. Every operation is idempotent — roles are
inserted only when missing, and the admin user only when its email is absent.
"""
