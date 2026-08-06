"""API / transfer schemas.

Pydantic models used at the boundaries of the application: request bodies,
response payloads, and validation. Domain entities are mapped to/from these
schemas in the API layer. Do not couple these to ORM models.
"""
