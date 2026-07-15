import uuid
from abc import ABC, abstractmethod

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.infrastructure.database.models import (
    AgentInsightRecord,
    ApprovalWorkflow,
    Invoice,
    InvoiceException,
    InvoiceStatus,
    User,
    Vendor,
)


class InvoiceRepository(ABC):
    @abstractmethod
    async def get_by_id(self, invoice_id: uuid.UUID) -> Invoice | None:
        ...

    @abstractmethod
    async def list_invoices(
        self, skip: int = 0, limit: int = 50, status: InvoiceStatus | None = None
    ) -> list[Invoice]:
        ...


class SQLAlchemyInvoiceRepository(InvoiceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, invoice_id: uuid.UUID) -> Invoice | None:
        result = await self.session.execute(
            select(Invoice)
            .options(
                selectinload(Invoice.vendor),
                selectinload(Invoice.exceptions),
                selectinload(Invoice.approvals),
                selectinload(Invoice.agent_insights),
            )
            .where(Invoice.id == invoice_id)
        )
        return result.scalar_one_or_none()

    async def get_by_number_and_vendor(
        self, invoice_number: str, vendor_id: uuid.UUID
    ) -> Invoice | None:
        result = await self.session.execute(
            select(Invoice).where(
                Invoice.invoice_number == invoice_number,
                Invoice.vendor_id == vendor_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_invoices(
        self, skip: int = 0, limit: int = 50, status: InvoiceStatus | None = None
    ) -> list[Invoice]:
        query = select(Invoice).options(selectinload(Invoice.vendor)).order_by(Invoice.created_at.desc())
        if status:
            query = query.where(Invoice.status == status)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, invoice: Invoice) -> Invoice:
        self.session.add(invoice)
        await self.session.flush()
        await self.session.refresh(invoice)
        return invoice

    async def update(self, invoice: Invoice) -> Invoice:
        await self.session.flush()
        await self.session.refresh(invoice)
        return invoice

    async def count_by_status(self) -> dict[str, int]:
        result = await self.session.execute(
            select(Invoice.status, func.count(Invoice.id)).group_by(Invoice.status)
        )
        return {row[0].value: row[1] for row in result.all()}

    async def get_dashboard_metrics(self) -> dict:
        total = await self.session.scalar(select(func.count(Invoice.id)))
        pending = await self.session.scalar(
            select(func.count(Invoice.id)).where(Invoice.status == InvoiceStatus.PENDING_APPROVAL)
        )
        auto_approved = await self.session.scalar(
            select(func.count(Invoice.id)).where(Invoice.auto_approved.is_(True))
        )
        avg_processing = await self.session.scalar(select(func.avg(Invoice.processing_time_ms)))
        total_amount = await self.session.scalar(select(func.sum(Invoice.total_amount)))
        avg_risk = await self.session.scalar(select(func.avg(Invoice.risk_score)))
        fraud_alerts = await self.session.scalar(
            select(func.count(Invoice.id)).where(Invoice.fraud_score >= 70)
        )
        return {
            "total_invoices": total or 0,
            "pending_invoices": pending or 0,
            "auto_approvals": auto_approved or 0,
            "avg_processing_time_ms": float(avg_processing or 0),
            "total_invoice_value": float(total_amount or 0),
            "avg_risk_score": float(avg_risk or 0),
            "fraud_alerts": fraud_alerts or 0,
        }


class VendorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, vendor_id: uuid.UUID) -> Vendor | None:
        result = await self.session.execute(select(Vendor).where(Vendor.id == vendor_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Vendor | None:
        result = await self.session.execute(
            select(Vendor).where(func.lower(Vendor.name) == name.lower())
        )
        return result.scalar_one_or_none()

    async def list_vendors(self, skip: int = 0, limit: int = 100) -> list[Vendor]:
        result = await self.session.execute(
            select(Vendor).order_by(Vendor.trust_score.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, vendor: Vendor) -> Vendor:
        self.session.add(vendor)
        await self.session.flush()
        await self.session.refresh(vendor)
        return vendor


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user


class ExceptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_bulk(self, exceptions: list[InvoiceException]) -> list[InvoiceException]:
        self.session.add_all(exceptions)
        await self.session.flush()
        return exceptions

    async def list_open(self, limit: int = 100) -> list[InvoiceException]:
        from backend.app.infrastructure.database.models import ExceptionStatus

        result = await self.session.execute(
            select(InvoiceException)
            .options(selectinload(InvoiceException.invoice))
            .where(InvoiceException.status == ExceptionStatus.OPEN)
            .order_by(InvoiceException.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_category(self) -> dict[str, int]:
        result = await self.session.execute(
            select(InvoiceException.category, func.count(InvoiceException.id)).group_by(
                InvoiceException.category
            )
        )
        return {row[0]: row[1] for row in result.all()}


class WorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_routes(self, routes: list[ApprovalWorkflow]) -> list[ApprovalWorkflow]:
        self.session.add_all(routes)
        await self.session.flush()
        return routes


class InsightRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_bulk(self, insights: list[AgentInsightRecord]) -> list[AgentInsightRecord]:
        self.session.add_all(insights)
        await self.session.flush()
        return insights
