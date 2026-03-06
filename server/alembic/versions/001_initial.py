"""Initial database schema

Revision ID: 001_initial
Revises:
Create Date: 2026-03-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Sessions table
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("agent_name", sa.String(), nullable=False, server_default="unnamed"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_events", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_tokens_input", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens_output", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Trace events table
    op.create_table(
        "trace_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_event_id", sa.String(), sa.ForeignKey("trace_events.id"), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("event_name", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("input_data", sa.Text(), nullable=True),
        sa.Column("output_data", sa.Text(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("tokens_input", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_output", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(), nullable=False, server_default="success"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trace_events_session_id", "trace_events", ["session_id"])
    op.create_index("ix_trace_events_event_type", "trace_events", ["event_type"])
    op.create_index("ix_trace_events_timestamp", "trace_events", ["timestamp"])

    # Memory entries table
    op.create_table(
        "memory_entries",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False, server_default="default"),
        sa.Column("memory_key", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("influenced_events", sa.Text(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Hallucination alerts table
    op.create_table(
        "hallucination_alerts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trace_event_id", sa.String(), sa.ForeignKey("trace_events.id"), nullable=False),
        sa.Column("source_event_id", sa.String(), sa.ForeignKey("trace_events.id"), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("expected_value", sa.Text(), nullable=False),
        sa.Column("actual_value", sa.Text(), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("hallucination_alerts")
    op.drop_table("memory_entries")
    op.drop_index("ix_trace_events_timestamp", "trace_events")
    op.drop_index("ix_trace_events_event_type", "trace_events")
    op.drop_index("ix_trace_events_session_id", "trace_events")
    op.drop_table("trace_events")
    op.drop_table("sessions")
