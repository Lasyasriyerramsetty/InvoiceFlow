import time
import uuid
from typing import Any

import structlog

from agents.contract_intelligence.agent import ContractIntelligenceAgent
from agents.document_intake.agent import DocumentIntakeAgent
from agents.exception_detection.agent import ExceptionDetectionAgent
from agents.finance_policy.agent import FinancePolicyAgent
from agents.fraud_intelligence.agent import FraudIntelligenceAgent
from agents.invoice_understanding.agent import InvoiceUnderstandingAgent
from agents.po_matching.agent import POMatchingAgent
from agents.recommendation.agent import RecommendationAgent
from agents.reporting.agent import ReportingAgent
from agents.workflow.agent import WorkflowAgent
from shared.schemas.agent_outputs import ProcessingPipelineResult

logger = structlog.get_logger(__name__)


class InvoiceProcessingPipeline:
    """LangGraph-style sequential multi-agent orchestrator for invoice processing."""

    def __init__(self) -> None:
        self.agents = {
            "intake": DocumentIntakeAgent(),
            "understanding": InvoiceUnderstandingAgent(),
            "contract": ContractIntelligenceAgent(),
            "po_matching": POMatchingAgent(),
            "policy": FinancePolicyAgent(),
            "exceptions": ExceptionDetectionAgent(),
            "fraud": FraudIntelligenceAgent(),
            "recommendation": RecommendationAgent(),
            "workflow": WorkflowAgent(),
            "reporting": ReportingAgent(),
        }

    async def run(
        self,
        invoice_id: str,
        document_bytes: bytes,
        filename: str,
        context: dict[str, Any] | None = None,
    ) -> ProcessingPipelineResult:
        start = time.perf_counter()
        pipeline_id = str(uuid.uuid4())
        ctx: dict[str, Any] = {
            "invoice_id": invoice_id,
            "document_bytes": document_bytes,
            "filename": filename,
            **(context or {}),
        }
        all_insights = []

        stages = [
            ("intake", self._run_intake),
            ("understanding", self._run_understanding),
            ("contract", self._run_contract),
            ("po_matching", self._run_po_matching),
            ("policy", self._run_policy),
            ("exceptions", self._run_exceptions),
            ("fraud", self._run_fraud),
            ("recommendation", self._run_recommendation),
            ("workflow", self._run_workflow),
            ("reporting", self._run_reporting),
        ]

        results: dict[str, Any] = {}
        for stage_name, runner in stages:
            try:
                stage_result = await runner(ctx)
                ctx.update(stage_result)
                results[stage_name] = stage_result
                if "insight" in stage_result and stage_result["insight"]:
                    all_insights.append(stage_result["insight"])
                    ctx.setdefault("_insights", []).append(stage_result["insight"])
                logger.info("pipeline_stage_complete", stage=stage_name, invoice_id=invoice_id)
            except Exception as exc:
                logger.error("pipeline_stage_failed", stage=stage_name, error=str(exc))
                raise

        ctx["all_insights"] = all_insights
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        return ProcessingPipelineResult(
            pipeline_id=pipeline_id,
            invoice_id=invoice_id,
            status="completed",
            classification=ctx.get("classification", {}),
            extracted_invoice=ctx.get("extracted_invoice", {}),
            contract_clauses=ctx.get("contract_clauses", []),
            po_match_result=ctx.get("po_match_result", {}),
            policy_validation=ctx.get("policy_validation", {}),
            exceptions=ctx.get("exceptions", []),
            fraud_assessment=ctx.get("fraud_assessment"),
            risk_score=ctx.get("risk_score"),
            recommendation=ctx.get("recommendation"),
            workflow_routes=ctx.get("workflow_routes", []),
            agent_insights=all_insights,
            processing_time_ms=elapsed_ms,
        )

    async def _run_intake(self, ctx: dict) -> dict:
        return await self.agents["intake"].execute(ctx)

    async def _run_understanding(self, ctx: dict) -> dict:
        return await self.agents["understanding"].execute(ctx)

    async def _run_contract(self, ctx: dict) -> dict:
        return await self.agents["contract"].execute(ctx)

    async def _run_po_matching(self, ctx: dict) -> dict:
        return await self.agents["po_matching"].execute(ctx)

    async def _run_policy(self, ctx: dict) -> dict:
        return await self.agents["policy"].execute(ctx)

    async def _run_exceptions(self, ctx: dict) -> dict:
        return await self.agents["exceptions"].execute(ctx)

    async def _run_fraud(self, ctx: dict) -> dict:
        return await self.agents["fraud"].execute(ctx)

    async def _run_recommendation(self, ctx: dict) -> dict:
        if "_insights" not in ctx:
            ctx["_insights"] = []
        return await self.agents["recommendation"].execute(ctx)

    async def _run_workflow(self, ctx: dict) -> dict:
        return await self.agents["workflow"].execute(ctx)

    async def _run_reporting(self, ctx: dict) -> dict:
        return await self.agents["reporting"].execute(ctx)
