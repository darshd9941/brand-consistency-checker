"""FastAPI API for programmatic brand consistency checking."""

from __future__ import annotations

import io
import json
import tempfile
import os
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from .brand_schema import BrandSpec
from .checker import BrandChecker, Severity

app = FastAPI(
    title="Brand Consistency Checker API",
    description="Validates AI-generated outputs against brand rules.",
    version="0.1.0",
)


def _result_to_dict(result) -> dict:
    return {
        "passed": result.passed,
        "score": result.score,
        "checked_items": result.checked_items,
        "passed_items": result.passed_items,
        "violations": [
            {
                "rule": v.rule,
                "message": v.message,
                "severity": v.severity.value,
                "context": v.context,
            }
            for v in result.violations
        ],
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/check/text")
async def check_text(
    spec: UploadFile = File(...),
    text: str = Form(...),
) -> dict:
    """Check text content against brand voice/tone rules."""
    spec_data = json.loads(await spec.read())
    brand = BrandSpec(**spec_data)
    checker = BrandChecker(brand)
    result = checker.check_text(text)
    return _result_to_dict(result)


@app.post("/check/image")
async def check_image(
    spec: UploadFile = File(...),
    image: UploadFile = File(...),
) -> dict:
    """Check an image against brand color palette and logo rules."""
    spec_data = json.loads(await spec.read())
    brand = BrandSpec(**spec_data)

    suffix = os.path.splitext(image.filename or "img.png")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await image.read())
        tmp_path = tmp.name

    try:
        checker = BrandChecker(brand)
        result = checker.check_image(tmp_path)
    finally:
        os.unlink(tmp_path)

    return _result_to_dict(result)


@app.post("/check/batch")
async def check_batch(
    spec: UploadFile = File(...),
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
) -> dict:
    """Run multiple checks in a single request."""
    spec_data = json.loads(await spec.read())
    brand = BrandSpec(**spec_data)
    checker = BrandChecker(brand)

    results: dict = {}

    if text:
        results["text"] = _result_to_dict(checker.check_text(text))

    if image:
        suffix = os.path.splitext(image.filename or "img.png")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await image.read())
            tmp_path = tmp.name
        try:
            results["image"] = _result_to_dict(checker.check_image(tmp_path))
        finally:
            os.unlink(tmp_path)

    if not results:
        raise HTTPException(status_code=400, detail="Provide text and/or image")

    # Overall pass/fail
    all_passed = all(
        r.get("passed", True) for r in results.values()
    )
    results["overall_passed"] = all_passed

    return results


@app.post("/spec/validate")
async def validate_spec(spec: UploadFile = File(...)) -> dict:
    """Validate a brand spec file itself."""
    try:
        spec_data = json.loads(await spec.read())
        brand = BrandSpec(**spec_data)
        return {
            "valid": True,
            "brand_name": brand.brand_name,
            "colors_count": len(brand.colors),
            "typography_count": len(brand.typography),
            "has_logo_rules": brand.logo is not None,
            "has_voice_rules": brand.voice is not None,
        }
    except Exception as exc:
        return {"valid": False, "error": str(exc)}


def main() -> None:
    """Run with uvicorn."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
