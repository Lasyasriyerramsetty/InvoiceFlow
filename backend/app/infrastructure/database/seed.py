import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import get_password_hash
from backend.app.infrastructure.database.models import (
    User,
    UserRole,
    Vendor,
    Contract,
    PurchaseOrder,
    Invoice,
    InvoiceStatus,
    InvoiceException,
    ExceptionStatus,
    ApprovalWorkflow,
    AgentInsightRecord,
    AuditLog,
)
from backend.app.infrastructure.database.session import AsyncSessionLocal, engine


async def seed_data():
    # NOTE: schema must already exist (run `alembic upgrade head` first).
    # We no longer call Base.metadata.create_all here.
    async with AsyncSessionLocal() as session:
        # Create default users
        print("Seeding users...")
        password_hash = get_password_hash("password123")
        users = [
            User(
                email="clerk@enterprise.com",
                hashed_password=password_hash,
                full_name="Alice Clerk",
                role=UserRole.AP_CLERK,
                department="Finance - Accounts Payable",
            ),
            User(
                email="manager@enterprise.com",
                hashed_password=password_hash,
                full_name="Bob Manager",
                role=UserRole.FINANCE_MANAGER,
                department="Finance",
            ),
            User(
                email="procurement@enterprise.com",
                hashed_password=password_hash,
                full_name="Peter Procurement",
                role=UserRole.PROCUREMENT,
                department="Procurement",
            ),
            User(
                email="legal@enterprise.com",
                hashed_password=password_hash,
                full_name="Linda Legal",
                role=UserRole.LEGAL,
                department="Legal & Compliance",
            ),
            User(
                email="cfo@enterprise.com",
                hashed_password=password_hash,
                full_name="Carl CFO",
                role=UserRole.CFO,
                department="Executive",
            ),
        ]
        
        for u in users:
            session.add(u)
        await session.flush()
        
        # Create vendors
        print("Seeding vendors...")
        vendors = [
            Vendor(
                vendor_code="VND-ACME",
                name="Acme Corporation Pvt Ltd",
                tax_id="GST-27AABCA1234A1Z5",
                gst_number="27AABCA1234A1Z5",
                country="IN",
                currency="INR",
                payment_terms="Net 30",
                trust_score=82.0,
                contract_health_score=88.0,
            ),
            Vendor(
                vendor_code="VND-GLOBTECH",
                name="Global Tech Solutions",
                tax_id="US-998877665",
                country="US",
                currency="USD",
                payment_terms="Net 45",
                trust_score=95.0,
                contract_health_score=98.0,
            ),
            Vendor(
                vendor_code="VND-VERTEX",
                name="Vertex Systems Inc",
                tax_id="US-112233445",
                country="US",
                currency="USD",
                payment_terms="Net 15",
                trust_score=42.0,
                contract_health_score=55.0,
            ),
            Vendor(
                vendor_code="VND-ORION",
                name="Orion Logistics",
                tax_id="DE-445566778",
                country="DE",
                currency="EUR",
                payment_terms="Net 30",
                trust_score=88.0,
                contract_health_score=75.0,
            ),
        ]
        
        for v in vendors:
            session.add(v)
        await session.flush()
        
        v_acme = vendors[0]
        v_glob = vendors[1]
        v_vertex = vendors[2]
        v_orion = vendors[3]
        
        # Create contracts
        print("Seeding contracts...")
        contracts = [
            Contract(
                contract_number="CON-ACME-001",
                vendor_id=v_acme.id,
                title="Service Level Agreement & Procurement Agreement",
                start_date=datetime.now(timezone.utc) - timedelta(days=180),
                end_date=datetime.now(timezone.utc) + timedelta(days=180),
                total_value=2500000.0,
                currency="INR",
                status="active",
                health_score=88.0,
                clauses_json={
                    "pricing": "Clause 4.2: Unit prices shall not exceed 3% annual revision without prior written consent.",
                    "payment_terms": "Clause 3.1: Payments are Net 30 days from the invoice date.",
                    "discounts": "Clause 3.2: 2% early payment discount if paid within 10 days.",
                }
            ),
            Contract(
                contract_number="CON-GLOB-002",
                vendor_id=v_glob.id,
                title="Master IT Software & Consulting Services",
                start_date=datetime.now(timezone.utc) - timedelta(days=365),
                end_date=datetime.now(timezone.utc) + timedelta(days=365),
                total_value=500000.0,
                currency="USD",
                status="active",
                health_score=98.0,
                clauses_json={
                    "pricing": "Clause 5.1: Software licensing fees are locked for the contract duration.",
                    "payment_terms": "Clause 4.2: Net 45 days upon receipt of verified goods receipt note.",
                }
            ),
            Contract(
                contract_number="CON-VERT-003",
                vendor_id=v_vertex.id,
                title="On-Demand Engineering Resource Staffing",
                start_date=datetime.now(timezone.utc) - timedelta(days=90),
                end_date=datetime.now(timezone.utc) - timedelta(days=10),  # Expired!
                total_value=120000.0,
                currency="USD",
                status="expired",
                health_score=45.0,
                clauses_json={
                    "pricing": "Clause 2.1: Developer hourly rate is capped at $75/hour.",
                    "payment_terms": "Clause 3.1: Net 15 days.",
                }
            ),
        ]
        
        for c in contracts:
            session.add(c)
        await session.flush()
        
        c_acme = contracts[0]
        c_glob = contracts[1]
        c_vertex = contracts[2]

        # Create purchase orders
        print("Seeding purchase orders...")
        purchase_orders = [
            PurchaseOrder(
                po_number="PO-ACME-8891",
                vendor_id=v_acme.id,
                department="Engineering",
                requester="Alice Smith",
                order_date=datetime.now(timezone.utc) - timedelta(days=30),
                total_amount=91500.0,
                currency="INR",
                status="open",
                line_items_json=[
                    {"line_number": 1, "description": "Cloud Services License", "quantity": 100, "unit_price": 425.0, "total_amount": 42500.0},
                    {"line_number": 2, "description": "Implementation Support", "quantity": 40, "unit_price": 850.0, "total_amount": 34000.0},
                    {"line_number": 3, "description": "Annual Maintenance", "quantity": 1, "unit_price": 15000.0, "total_amount": 15000.0},
                ],
                goods_receipt_json={"received_quantity": 91500.0}
            ),
            PurchaseOrder(
                po_number="PO-GLOB-1002",
                vendor_id=v_glob.id,
                department="IT",
                requester="John Doe",
                order_date=datetime.now(timezone.utc) - timedelta(days=20),
                total_amount=120000.0,
                currency="USD",
                status="open",
                line_items_json=[
                    {"line_number": 1, "description": "Enterprise API Gateway Support", "quantity": 1, "unit_price": 120000.0, "total_amount": 120000.0}
                ],
                goods_receipt_json={"received_quantity": 120000.0}
            ),
            PurchaseOrder(
                po_number="PO-VERT-3044",
                vendor_id=v_vertex.id,
                department="Product Management",
                requester="Bob Jones",
                order_date=datetime.now(timezone.utc) - timedelta(days=15),
                total_amount=45000.0,
                currency="USD",
                status="open",
                line_items_json=[
                    {"line_number": 1, "description": "Contract Engineering Support", "quantity": 600, "unit_price": 75.0, "total_amount": 45000.0}
                ],
                goods_receipt_json={"received_quantity": 45000.0}
            )
        ]
        
        for po in purchase_orders:
            session.add(po)
        await session.flush()
        
        po_acme = purchase_orders[0]
        po_glob = purchase_orders[1]
        po_vertex = purchase_orders[2]

        # Create Invoices
        print("Seeding invoices...")
        invoices = [
            # 1. Clean, Approved Invoice
            Invoice(
                invoice_number="INV-2024-001",
                vendor_id=v_acme.id,
                po_id=po_acme.id,
                contract_id=c_acme.id,
                status=InvoiceStatus.APPROVED,
                invoice_date=datetime.now(timezone.utc) - timedelta(days=5),
                due_date=datetime.now(timezone.utc) + timedelta(days=25),
                currency="INR",
                subtotal=91500.0,
                tax_amount=16470.0,
                total_amount=107970.0,
                payment_terms="Net 30",
                extracted_data_json={
                    "invoice_number": "INV-2024-001",
                    "vendor_name": v_acme.name,
                    "po_number": po_acme.po_number,
                    "currency": "INR",
                    "subtotal": 91500.0,
                    "tax_amount": 16470.0,
                    "total_amount": 107970.0,
                    "payment_terms": "Net 30",
                    "line_items": po_acme.line_items_json
                },
                risk_score=5.0,
                fraud_score=3.0,
                health_score=95.0,
                compliance_score=100.0,
                auto_approved=True,
                processing_time_ms=1850,
                ai_summary="Invoice INV-2024-001 fully matches purchase order PO-ACME-8891 and complies with Contract CON-ACME-001. System initiated auto-approval."
            ),
            # 2. Invoice with Price Mismatch Exception
            Invoice(
                invoice_number="INV-2024-1456",
                vendor_id=v_acme.id,
                po_id=po_acme.id,
                contract_id=c_acme.id,
                status=InvoiceStatus.PENDING_APPROVAL,
                invoice_date=datetime.now(timezone.utc) - timedelta(days=2),
                due_date=datetime.now(timezone.utc) + timedelta(days=28),
                currency="INR",
                subtotal=96750.0,
                tax_amount=17415.0,
                total_amount=114165.0,
                payment_terms="Net 30",
                extracted_data_json={
                    "invoice_number": "INV-2024-1456",
                    "vendor_name": v_acme.name,
                    "po_number": po_acme.po_number,
                    "currency": "INR",
                    "subtotal": 96750.0,
                    "tax_amount": 17415.0,
                    "total_amount": 114165.0,
                    "payment_terms": "Net 30",
                    "line_items": [
                        {"line_number": 1, "description": "Cloud Services License", "quantity": 100, "unit_price": 467.5, "total_amount": 46750.0}, # Over unit price 425 by 10%
                        {"line_number": 2, "description": "Implementation Support", "quantity": 40, "unit_price": 850.0, "total_amount": 34000.0},
                        {"line_number": 3, "description": "Annual Maintenance", "quantity": 1, "unit_price": 16000.0, "total_amount": 16000.0}, # Over 15000 by 6.6%
                    ]
                },
                risk_score=48.0,
                fraud_score=10.0,
                health_score=52.0,
                compliance_score=90.0,
                auto_approved=False,
                processing_time_ms=2100,
                ai_summary="Price mismatches detected. Cloud licensing unit price of ₹467.50 exceeds PO price of ₹425.00 (+10.0%). Annual maintenance of ₹16,000 exceeds ₹15,000 (+6.6%). This violates procurement policy and contract pricing guidelines."
            ),
            # 3. Invoice with Missing PO Exception
            Invoice(
                invoice_number="INV-VT-992",
                vendor_id=v_vertex.id,
                po_id=None,
                contract_id=c_vertex.id,
                status=InvoiceStatus.PENDING_APPROVAL,
                invoice_date=datetime.now(timezone.utc) - timedelta(days=4),
                due_date=datetime.now(timezone.utc) + timedelta(days=11),
                currency="USD",
                subtotal=24000.0,
                tax_amount=0.0,
                total_amount=24000.0,
                payment_terms="Net 15",
                extracted_data_json={
                    "invoice_number": "INV-VT-992",
                    "vendor_name": v_vertex.name,
                    "po_number": None,
                    "currency": "USD",
                    "subtotal": 24000.0,
                    "tax_amount": 0.0,
                    "total_amount": 24000.0,
                    "payment_terms": "Net 15",
                    "line_items": [
                        {"line_number": 1, "description": "Extra Development Work", "quantity": 300, "unit_price": 80.0, "total_amount": 24000.0} # Hourly rate is 80 instead of 75
                    ]
                },
                risk_score=72.0,
                fraud_score=25.0,
                health_score=28.0,
                compliance_score=40.0,
                auto_approved=False,
                processing_time_ms=1950,
                ai_summary="Missing PO reference on high-value invoice ($24,000 exceeds the $1,000 threshold). Additionally, the engineer hourly rate ($80.00) exceeds the contractual cap ($75.00) specified in Clause 2.1."
            ),
            # 4. Duplicate Invoice
            Invoice(
                invoice_number="INV-OR-7711",
                vendor_id=v_orion.id,
                po_id=None,
                contract_id=None,
                status=InvoiceStatus.REJECTED,
                invoice_date=datetime.now(timezone.utc) - timedelta(days=10),
                due_date=datetime.now(timezone.utc) + timedelta(days=20),
                currency="EUR",
                subtotal=8500.0,
                tax_amount=1615.0,
                total_amount=10115.0,
                payment_terms="Net 30",
                extracted_data_json={
                    "invoice_number": "INV-OR-7711",
                    "vendor_name": v_orion.name,
                    "po_number": None,
                    "currency": "EUR",
                    "subtotal": 8500.0,
                    "tax_amount": 1615.0,
                    "total_amount": 10115.0,
                    "payment_terms": "Net 30",
                    "line_items": [
                        {"line_number": 1, "description": "Freight and Custom Services", "quantity": 1, "unit_price": 8500.0, "total_amount": 8500.0}
                    ]
                },
                risk_score=95.0,
                fraud_score=98.0,
                health_score=5.0,
                compliance_score=10.0,
                auto_approved=False,
                processing_time_ms=1600,
                ai_summary="Critical fraud trigger. This invoice has the exact same invoice number (INV-OR-7711), vendor, and amount as a previously processed and paid invoice on 2026-06-15. Potential double billing fraud."
            ),
            # 5. Suspicious / Round Amounts Anomaly Invoice
            Invoice(
                invoice_number="INV-VT-999",
                vendor_id=v_vertex.id,
                po_id=po_vertex.id,
                contract_id=c_vertex.id,
                status=InvoiceStatus.ESCALATED,
                invoice_date=datetime.now(timezone.utc) - timedelta(days=1),
                due_date=datetime.now(timezone.utc) + timedelta(days=14),
                currency="USD",
                subtotal=49000.0,
                tax_amount=0.0,
                total_amount=49000.0,
                payment_terms="Net 15",
                extracted_data_json={
                    "invoice_number": "INV-VT-999",
                    "vendor_name": v_vertex.name,
                    "po_number": po_vertex.po_number,
                    "currency": "USD",
                    "subtotal": 49000.0,
                    "tax_amount": 0.0,
                    "total_amount": 49000.0,
                    "payment_terms": "Net 15",
                    "line_items": [
                        {"line_number": 1, "description": "Consulting Fee A", "quantity": 1, "unit_price": 20000.0, "total_amount": 20000.0},
                        {"line_number": 2, "description": "Consulting Fee B", "quantity": 1, "unit_price": 15000.0, "total_amount": 15000.0},
                        {"line_number": 3, "description": "Consulting Fee C", "quantity": 1, "unit_price": 14000.0, "total_amount": 14000.0},
                    ]
                },
                risk_score=85.0,
                fraud_score=68.0,
                health_score=15.0,
                compliance_score=30.0,
                auto_approved=False,
                processing_time_ms=2300,
                ai_summary="Multiple anomaly flags. Invoice contains multiple suspicious round amounts ($20k, $15k, $14k). Total amount $49,000 is just below the Director approval threshold of $50,000, suggesting a split invoice fraud attempt to bypass senior authorization."
            )
        ]
        
        for inv in invoices:
            session.add(inv)
        await session.flush()
        
        inv_approved = invoices[0]
        inv_price = invoices[1]
        inv_missing_po = invoices[2]
        inv_dup = invoices[3]
        inv_fraud = invoices[4]

        # Seed exceptions for each invoice
        print("Seeding exceptions...")
        exceptions = [
            # Exceptions for Price Mismatch Invoice
            InvoiceException(
                invoice_id=inv_price.id,
                category="price_mismatch",
                severity="high",
                title="Unit Price Mismatch",
                description="Cloud Services License unit price ₹467.50 exceeds PO unit price ₹425.00.",
                reasoning="Invoice INV-2024-1456 exceeds the contractual unit price by ₹42.50 per item, resulting in a projected overpayment of ₹4,250.00. Clause 4.2 of the procurement agreement limits price revisions to 3%. This exceeds that limit.",
                confidence=0.95,
                evidence_json={"actual_price": 467.5, "expected_price": 425.0, "line_item": 1},
                contract_clause="Clause 4.2 - Price Revision Limit",
                policy_reference="PROC-001 - Three Way Match Policy",
                suggested_resolution="Request credit note from vendor or obtain approval for price variance.",
                business_impact="Financial loss and breach of procurement SLA.",
                financial_impact=4250.00,
                estimated_loss=4250.00,
                status=ExceptionStatus.OPEN
            ),
            InvoiceException(
                invoice_id=inv_price.id,
                category="price_mismatch",
                severity="medium",
                title="Maintenance Price Escalation",
                description="Annual Maintenance price ₹16,000 exceeds PO price ₹15,000.",
                reasoning="Annual maintenance billed at ₹16,000, exceeding PO contract pricing by ₹1,000 (+6.6%). This exceeds the 3% permitted escalation variance.",
                confidence=0.88,
                evidence_json={"actual_price": 16000.0, "expected_price": 15000.0, "line_item": 3},
                contract_clause="Clause 4.2 - Price Revision Limit",
                policy_reference="PROC-001 - Three Way Match Policy",
                suggested_resolution="Short-pay invoice or request a corrected invoice from the supplier.",
                business_impact="Minor price inflation.",
                financial_impact=1000.00,
                estimated_loss=1000.00,
                status=ExceptionStatus.OPEN
            ),
            # Exceptions for Missing PO Invoice
            InvoiceException(
                invoice_id=inv_missing_po.id,
                category="missing_po",
                severity="high",
                title="Missing Purchase Order",
                description="No Purchase Order references found on invoice for $24,000.",
                reasoning="Finance Policy PROC-001 dictates that a valid PO is mandatory for all invoices exceeding $1,000. No PO number was provided by vendor or found in system database.",
                confidence=0.98,
                evidence_json={"invoice_total": 24000.0, "threshold": 1000.0},
                policy_reference="PROC-001 - Procurement PO Policy",
                suggested_resolution="Contact Bob Jones (Product Management) to request a retro-active PO or return invoice to vendor.",
                business_impact="Cannot post invoice to ledger without active PO matching.",
                financial_impact=24000.00,
                estimated_loss=0.0,
                status=ExceptionStatus.IN_REVIEW
            ),
            InvoiceException(
                invoice_id=inv_missing_po.id,
                category="price_mismatch",
                severity="medium",
                title="Hourly Consulting Rate Escalation",
                description="Consulting rate of $80.00/hour exceeds contract cap of $75.00/hour.",
                reasoning="Engineering resource charged at $80.00 per hour, which violates Clause 2.1 of Contract CON-VERT-003 limiting staffing hourly rate to $75.00.",
                confidence=0.91,
                evidence_json={"actual_rate": 80.0, "expected_rate": 75.0, "hours": 300},
                contract_clause="Clause 2.1 - Development Rate Cap",
                suggested_resolution="Short pay the invoice by $1,500.00 ($5 variance * 300 hours) or seek waiver from VP of Product.",
                business_impact="Vendor overbilling.",
                financial_impact=1500.00,
                estimated_loss=1500.00,
                status=ExceptionStatus.OPEN
            ),
            # Exceptions for Duplicate Invoice
            InvoiceException(
                invoice_id=inv_dup.id,
                category="duplicate_invoice",
                severity="critical",
                title="Duplicate Billing Detected",
                description="Invoice number INV-OR-7711 matches a paid invoice from Orion Logistics.",
                reasoning="System detected identical invoice number INV-OR-7711 for vendor Orion Logistics. An invoice with these exact parameters was paid on June 15, 2026.",
                confidence=0.99,
                evidence_json={"previous_invoice_id": str(uuid.uuid4()), "payment_date": "2026-06-15", "amount": 10115.0},
                policy_reference="FIN-009 - Duplicate Payment Protection",
                suggested_resolution="Reject invoice immediately. Notify the vendor that this bill has already been settled.",
                business_impact="Direct cash loss if paid twice.",
                financial_impact=10115.00,
                estimated_loss=10115.00,
                status=ExceptionStatus.OPEN
            ),
            # Exceptions for Anomaly/Split Invoice
            InvoiceException(
                invoice_id=inv_fraud.id,
                category="fraud_indicators",
                severity="high",
                title="Suspicious Round Amount Billing",
                description="Invoice contains multiple clean round amount line items.",
                reasoning="Line items consist of $20,000, $15,000, and $14,000. Having multiple round amounts on consulting services indicates potential invoice padding or lack of actual hourly audit records.",
                confidence=0.82,
                evidence_json={"amounts": [20000.0, 15000.0, 14000.0]},
                policy_reference="FIN-015 - Anti-Fraud & Compliance",
                suggested_resolution="Request timesheets and deliverables reports from Vertex Systems to audit consulting hours.",
                business_impact="Potential consulting overpayment.",
                financial_impact=49000.00,
                estimated_loss=15000.00,
                status=ExceptionStatus.OPEN
            ),
            InvoiceException(
                invoice_id=inv_fraud.id,
                category="fraud_indicators",
                severity="high",
                title="Potential Threshold Split Invoice",
                description="Total amount of $49,000 is directly below the $50,000 Director approval limit.",
                reasoning="Statistical analysis shows this invoice is grouped right under the $50,000 threshold. When compared to Vertex's history, this is 120% higher than average. This strongly suggests split-billing to avoid Director-level approval.",
                confidence=0.90,
                evidence_json={"invoice_total": 49000.0, "threshold": 50000.0, "average_spend": 22000.0},
                policy_reference="FIN-001 - Approval Authority Matrix",
                suggested_resolution="Route to Director for explicit approval despite falling below the threshold.",
                business_impact="Circumvention of internal controls.",
                financial_impact=0.0,
                estimated_loss=0.0,
                status=ExceptionStatus.OPEN
            )
        ]
        
        for exc in exceptions:
            session.add(exc)
        await session.flush()

        # Seed approval workflows
        print("Seeding approval workflows...")
        workflows = [
            # Approved Invoice Route
            ApprovalWorkflow(
                invoice_id=inv_approved.id,
                approver_role="AP Clerk",
                department="Accounts Payable",
                priority=1,
                status="approved",
                reason="Automatic matching success. Safe transaction score.",
                sla_hours=8,
                decided_at=datetime.now(timezone.utc) - timedelta(days=5),
                comments="System auto-approved because risk score is minimal."
            ),
            # Price Mismatch Invoice Route
            ApprovalWorkflow(
                invoice_id=inv_price.id,
                approver_role="AP Clerk",
                department="Accounts Payable",
                priority=1,
                status="approved",
                reason="Initial screening complete. Route to Procurement for variance waiver.",
                sla_hours=8,
                decided_at=datetime.now(timezone.utc) - timedelta(days=1),
                comments="Forwarded to Procurement due to unit price mismatch."
            ),
            ApprovalWorkflow(
                invoice_id=inv_price.id,
                approver_role="Procurement Manager",
                department="Procurement",
                priority=2,
                status="pending",
                reason="PO price mismatch requires procurement investigation and vendor contact.",
                sla_hours=24
            ),
            # Missing PO Invoice Route
            ApprovalWorkflow(
                invoice_id=inv_missing_po.id,
                approver_role="Finance Manager",
                department="Finance",
                priority=1,
                status="pending",
                reason="Required due to missing PO on invoice > $1,000.",
                sla_hours=24
            ),
            ApprovalWorkflow(
                invoice_id=inv_missing_po.id,
                approver_role="Procurement Manager",
                department="Procurement",
                priority=2,
                status="pending",
                reason="Required to generate retroactive PO reference.",
                sla_hours=24
            ),
            # Duplicate Invoice Route
            ApprovalWorkflow(
                invoice_id=inv_dup.id,
                approver_role="Finance Manager",
                department="Finance",
                priority=1,
                status="rejected",
                reason="Rejected due to duplicate billing match on invoice INV-OR-7711.",
                sla_hours=24,
                decided_at=datetime.now(timezone.utc) - timedelta(days=9),
                comments="Duplicate invoice. Rejected."
            ),
            # Fraud Invoice Route
            ApprovalWorkflow(
                invoice_id=inv_fraud.id,
                approver_role="Legal & Compliance",
                department="Legal",
                priority=1,
                status="pending",
                reason="Fraud and split-billing warnings require compliance review.",
                sla_hours=12
            ),
            ApprovalWorkflow(
                invoice_id=inv_fraud.id,
                approver_role="Finance Director",
                department="Finance",
                priority=2,
                status="pending",
                reason="Capping risk thresholds. Requires senior management override.",
                sla_hours=48
            )
        ]
        
        for wf in workflows:
            session.add(wf)
        await session.flush()

        # Seed agent insights
        print("Seeding agent insights...")
        insights = [
            # Insights for Price Mismatch Invoice
            AgentInsightRecord(
                invoice_id=inv_price.id,
                agent_name="DocumentIntakeAgent",
                reasoning="Invoice classified as invoice with 98% confidence. OCR successful using pypdf fallback. Image print quality clear.",
                confidence=0.98,
                evidence_json={"pages": 1, "chars": 1520}
            ),
            AgentInsightRecord(
                invoice_id=inv_price.id,
                agent_name="InvoiceUnderstandingAgent",
                reasoning="Successfully extracted invoice number INV-2024-1456, total ₹114,165.00 and 3 line items. Extraction confidence 96%.",
                confidence=0.96,
                evidence_json={"invoice_number": "INV-2024-1456", "total_amount": 114165.0}
            ),
            AgentInsightRecord(
                invoice_id=inv_price.id,
                agent_name="POMatchingAgent",
                reasoning="3-way matching failed. Match score 65/100. Price differences detected on line items 1 and 3.",
                confidence=0.90,
                evidence_json={"mismatches": 2, "match_score": 65}
            ),
            AgentInsightRecord(
                invoice_id=inv_price.id,
                agent_name="ContractIntelligenceAgent",
                reasoning="Matched contract CON-ACME-001. Clause 4.2 restricts price revisions to a maximum of 3%. Invoice exceeds this rate.",
                confidence=0.88,
                evidence_json={"contract_id": "CON-ACME-001"}
            ),
            
            # Insights for Fraud Invoice
            AgentInsightRecord(
                invoice_id=inv_fraud.id,
                agent_name="FraudIntelligenceAgent",
                reasoning="Statistical flags triggered: Benford digit distribution suspicious for consulting fees. Invoice amount ($49,000) is just 2% below senior sign-off threshold of $50,000.",
                confidence=0.85,
                evidence_json={"indicators": ["split_invoice", "round_off_fraud"]}
            ),
            AgentInsightRecord(
                invoice_id=inv_fraud.id,
                agent_name="RecommendationAgent",
                reasoning="Recommend immediate hold and escalation to Compliance. Financial impact is high ($49,000) with a vendor of low trust score (42.0). Risk is critical.",
                confidence=0.82,
                evidence_json={"risk_level": "critical", "estimated_loss": 15000.0}
            )
        ]
        
        for ins in insights:
            session.add(ins)
        await session.flush()

        # Seed audit logs
        print("Seeding audit logs...")
        logs = [
            AuditLog(
                action="USER_LOGIN",
                resource_type="auth",
                ip_address="127.0.0.1",
                details_json={"email": "manager@enterprise.com", "status": "success"}
            ),
            AuditLog(
                action="INVOICE_UPLOADED",
                resource_type="invoice",
                resource_id=str(inv_price.id),
                details_json={"filename": "invoice_acme_price_mismatch.pdf", "uploader": "clerk@enterprise.com"}
            ),
            AuditLog(
                action="EXCEPTION_FLAGGED",
                resource_type="exception",
                resource_id=str(inv_price.id),
                details_json={"agent": "ExceptionDetectionAgent", "count": 2}
            ),
            AuditLog(
                action="INVOICE_REJECTED",
                resource_type="invoice",
                resource_id=str(inv_dup.id),
                details_json={"reason": "Duplicate invoice INV-OR-7711", "actor": "manager@enterprise.com"}
            )
        ]
        
        for l in logs:
            session.add(l)
            
        await session.commit()
        print("Database seeded successfully!")


if __name__ == "__main__":
    # Import and run async main
    import sys
    print("Starting database seeding...")
    asyncio.run(seed_data())
