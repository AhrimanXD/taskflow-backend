"""Central ID generator.

We use UUIDv7 for primary keys: it embeds a millisecond timestamp in the high
bits, so ids sort by creation time (unlike random UUIDv4). That keeps B-tree
index inserts local and lets `ORDER BY id` stand in for "newest first".

`uuid_utils.compat.uuid7` returns a *stdlib* `uuid.UUID` (the bare
`uuid_utils.uuid7` returns a custom type that SQLAlchemy's `Uuid` won't accept).
"""

from uuid_utils.compat import uuid7

__all__ = ["uuid7"]
