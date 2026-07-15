"""Seed database with demo data for development and demos."""

import asyncio
import uuid
from datetime import datetime, timezone

from backend.app.core.security import get_password_hash
from backend.app.infrastructure.database.models import (
    Base,
    Contract,
    PurchaseOrder,
    User,
    UserRole,
    Vendor,
)
from backend.app.infrastructure.database.session import AsyncSessionLocal, engine


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        admin = User(
            email="admin@ap-agent.com",
            hashed_password=get_password_hash("Admin@123456"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            department="IT",
        )
        fm = User(
            email="finance@ap-agent.com",
            hashed_password=get_password_hash("Finance@123456"),
            full_name="Sarah Chen",
            role=UserRole.FINANCE_MANAGER,
            department="Finance",
        )
        session.add_all([admin, fm])

        vendor = Vendor(
            vendor_code="VND-ACME-001",
            name="Acme Corporation Pvt Ltd",
            tax_id="AABCA1234A",
            gst_number="27AABCA1234A1Z5",
            country="IN",
            currency="INR",
            payment_terms="Net 30",
            trust_score=82.0,
            contract_health_score=88.0,
        )
        session.add(vendor)
        await session.flush()

        contract = Contract(
            contract_number="CTR-2024-ACME-001",
            vendor_id=vendor.id,
            title="Enterprise Cloud Services Agreement",
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2027, 1, 1, tzinfo=timezone.utc),
            total_value=2400000,
            currency="INR",
            health_score=88.0,
            clauses_json={
                "pricing": "Max 3% price increase without approval (Clause 4.2)",
                "payment": "Net 30 with 2% early payment discount",
            },
        )
        session.add(contract)

        po = PurchaseOrder(
            po_number="PO-2024-8891",
            vendor_id=vendor.id,
            department="IT",
            requester="John Smith",
            order_date=datetime(2024, 5, 1, tzinfo=timezone.utc),
            total_amount=104850.00,
            currency="INR",
            status="open",
            line_items_json=[
                {"line_number": 1, "description": "Cloud Services License", "quantity": 100, "unit_price": 425.00, "total_amount": 42500.00},
                {"line_number": 2, "description": "Implementation Support", "quantity": 40, "unit_price": 850.00, "total_amount": 34000.00},
                {"line_number": 3, "description": "Annual Maintenance", "quantity": 1, "unit_price": 15000.00, "total_amount": 15000.00},
            ],
            goods_receipt_json={"received_quantity": 104850.00, "status": "complete"},
        )
        session.add(po)

        await session.commit()
        print("Seed data created successfully!")
        print("  Admin: admin@ap-agent.com / Admin@123456")
        print("  Finance Manager: finance@ap-agent.com / Finance@123456")


if __name__ == "__main__":
    asyncio.run(seed())
