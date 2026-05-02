from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional
import json

from app.core.scanner import StaticScanner
from app.core import integrity
from app import db

router = APIRouter()
scanner = StaticScanner()

class ScanRequest(BaseModel):
    model_config = ConfigDict(extra='allow')

class ApproveRequest(BaseModel):
    tool_id: str
    name: str
    config: Dict[str, Any]

class VerifyRequest(BaseModel):
    tool_id: str
    config: Dict[str, Any]

class BlockRequest(BaseModel):
    tool_id: str
    reason: str = "Manually blocked by admin."

class ReverifyRequest(BaseModel):
    tool_id: str
    config: Dict[str, Any]

@router.post("/scan")
async def scan_config(request: Request):
    try:
        config = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    results = scanner.scan_config(config)

    severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    max_severity = "LOW"
    for r in results:
        if severity_order.get(r.severity, 0) > severity_order.get(max_severity, 0):
            max_severity = r.severity

    res_dicts = [r.to_dict() for r in results]

    return {
        "status": "success",
        "severity": max_severity if results else "SAFE",
        "findings": res_dicts,
        "is_safe": len(results) == 0
    }

@router.post("/approve")
async def approve_tool(req: ApproveRequest):
    canonical_hash = integrity.generate_canonical_hash(req.config)

    db.register_tool(
        tool_id=req.tool_id,
        name=req.name,
        status="APPROVED",
        severity="SAFE",
        approved_hash=canonical_hash
    )

    db.log_audit(
        action="APPROVE",
        result="SUCCESS",
        reason=f"Tool '{req.name}' explicitly approved by admin.",
        tool_id=req.tool_id
    )

    return {
        "status": "success",
        "message": "Tool approved and hashed securely.",
        "tool_id": req.tool_id,
        "approved_hash": canonical_hash
    }

@router.post("/verify")
async def verify_tool(req: VerifyRequest):
    tool = db.get_tool(req.tool_id)
    if not tool:
        db.log_audit("VERIFY", "BLOCK", "Tool not registered or unknown.", req.tool_id)
        return {"decision": "BLOCK", "reason": "Tool not registered.", "match": False, "current_hash": ""}

    if tool['status'] not in ("APPROVED", "RE-APPROVED"):
        db.log_audit("VERIFY", "BLOCK", f"Tool status is '{tool['status']}' — execution denied.", req.tool_id)
        return {"decision": "BLOCK", "reason": f"Tool is not in an approved state (status: {tool['status']}).", "match": False, "current_hash": ""}

    expected_hash = tool['approved_hash']
    current_hash = integrity.generate_canonical_hash(req.config)
    match = current_hash == expected_hash

    if match:
        db.log_audit("VERIFY", "ALLOW", "Integrity check passed. Execution authorized.", req.tool_id)
        return {"decision": "ALLOW", "reason": "Integrity validated. Configuration is unmodified.", "match": True, "current_hash": current_hash, "expected_hash": expected_hash}
    else:
        db.register_tool(
            tool_id=req.tool_id,
            name=tool['name'],
            status="MODIFIED",
            severity=tool['severity'],
            approved_hash=tool['approved_hash']
        )
        db.log_audit("VERIFY", "BLOCK", "Integrity mismatch detected — potential tool poisoning.", req.tool_id)
        return {"decision": "BLOCK", "reason": "Configuration integrity check failed. Potential tampering or tool poisoning detected.", "match": False, "current_hash": current_hash, "expected_hash": expected_hash}

@router.post("/block")
async def block_tool(req: BlockRequest):
    tool = db.get_tool(req.tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found.")

    db.register_tool(
        tool_id=req.tool_id,
        name=tool['name'],
        status="BLOCKED",
        severity=tool['severity'],
        approved_hash=tool.get('approved_hash')
    )

    db.log_audit(
        action="BLOCK",
        result="BLOCKED",
        reason=req.reason,
        tool_id=req.tool_id
    )

    return {"status": "success", "message": f"Tool '{tool['name']}' has been blocked.", "tool_id": req.tool_id}

@router.post("/reverify")
async def reverify_tool(req: ReverifyRequest):
    """Re-compute and update the canonical hash for an already-registered tool, transitioning it to RE-APPROVED."""
    tool = db.get_tool(req.tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found.")

    new_hash = integrity.generate_canonical_hash(req.config)

    db.register_tool(
        tool_id=req.tool_id,
        name=tool['name'],
        status="RE-APPROVED",
        severity=tool['severity'],
        approved_hash=new_hash
    )

    db.log_audit(
        action="RE-APPROVE",
        result="SUCCESS",
        reason=f"Tool '{tool['name']}' re-hashed and re-approved by admin.",
        tool_id=req.tool_id
    )

    return {"status": "success", "new_hash": new_hash, "tool_id": req.tool_id}

@router.get("/audit")
async def get_audit_logs():
    return db.get_audits()

@router.get("/tools")
async def get_tools():
    return db.get_all_tools()
