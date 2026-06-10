"""create_initial_tables

Revision ID: 6974fd53b60f
Revises: 
Create Date: 2026-06-09 20:04:05.260151

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6974fd53b60f"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables: user, profile, profile_follow, profile_channel."""

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "user",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("googleId", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("avatarUrl", sa.String(length=2048), nullable=True),
        sa.Column("accessToken", sa.String(length=2048), nullable=True),
        sa.Column("refreshToken", sa.String(length=2048), nullable=True),
        sa.Column(
            "createdAt",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updatedAt",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_user_email"),
    )

    # ------------------------------------------------------------------
    # profiles
    # ------------------------------------------------------------------
    op.create_table(
        "profile",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("userId", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("isDefault", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("isPublic", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "createdAt",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updatedAt",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["userId"], ["user.id"], name="fk_profile_userId", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_profile_userId", "profile", ["userId"], unique=False)

    # ------------------------------------------------------------------
    # profile_follows
    # ------------------------------------------------------------------
    op.create_table(
        "profile_follow",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("followerId", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("profileId", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "createdAt",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["followerId"],
            ["user.id"],
            name="fk_profile_follow_followerId",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["profileId"],
            ["profile.id"],
            name="fk_profile_follow_profileId",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "followerId", "profileId", name="uq_profile_follow"
        ),
    )
    op.create_index(
        "ix_profile_follow_followerId",
        "profile_follow",
        ["followerId"],
        unique=False,
    )
    op.create_index(
        "ix_profile_follow_profileId",
        "profile_follow",
        ["profileId"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # profile_channels
    # ------------------------------------------------------------------
    op.create_table(
        "profile_channel",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("profileId", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("youtubeChannelId", sa.String(length=255), nullable=False),
        sa.Column("channelTitle", sa.String(length=255), nullable=False),
        sa.Column("thumbnailUrl", sa.String(length=2048), nullable=True),
        sa.ForeignKeyConstraint(
            ["profileId"],
            ["profile.id"],
            name="fk_profile_channel_profileId",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_profile_channel_profileId",
        "profile_channel",
        ["profileId"],
        unique=False,
    )


def downgrade() -> None:
    """Drop all tables created by this migration."""

    op.drop_index("ix_profile_channel_profileId", table_name="profile_channel")
    op.drop_table("profile_channel")

    op.drop_index("ix_profile_follow_profileId", table_name="profile_follow")
    op.drop_index("ix_profile_follow_followerId", table_name="profile_follow")
    op.drop_table("profile_follow")

    op.drop_index("ix_profile_userId", table_name="profile")
    op.drop_table("profile")

    op.drop_table("user")

