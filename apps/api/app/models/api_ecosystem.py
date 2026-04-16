"""API & Ecosystem models — FM-201 through FM-208.

New tables:
- api_keys: API key authentication (FM-201)
- webhook_subscriptions: Webhook event subscriptions (FM-203)
- webhook_deliveries: Webhook delivery log with retry tracking (FM-203)
- connector_registry: Integration marketplace registry (FM-208)
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Boolean,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSON as PG_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


# ── FM-201: API Keys ─────────────────────────────────────────────


class APIKey(Base):
    """API key for programmatic access."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    scopes: Mapped[list] = mapped_column(PG_JSON, nullable=False, default=list)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ── FM-203: Webhook Subscriptions ────────────────────────────────


class WebhookSubscription(Base):
    """Webhook event subscription."""

    __tablename__ = "webhook_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    secret_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    events: Mapped[list] = mapped_column(PG_JSON, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookDelivery(Base):
    """Record of a webhook delivery attempt."""

    __tablename__ = "webhook_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status"),
        default=DeliveryStatus.PENDING,
        nullable=False,
    )
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ── FM-208: Integration Marketplace ──────────────────────────────


class ConnectorType(str, enum.Enum):
    SOURCE = "source"
    SINK = "sink"
    BIDIRECTIONAL = "bidirectional"


class ConnectorStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class ConnectorRegistry(Base):
    """Installed integration connector."""

    __tablename__ = "connector_registry"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    connector_type: Mapped[ConnectorType] = mapped_column(
        Enum(ConnectorType, name="connector_type"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config_json: Mapped[dict] = mapped_column(PG_JSON, nullable=False, default=dict)
    status: Mapped[ConnectorStatus] = mapped_column(
        Enum(ConnectorStatus, name="connector_status"),
        default=ConnectorStatus.ACTIVE,
        nullable=False,
    )
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_health_check: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
