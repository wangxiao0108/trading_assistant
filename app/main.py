from __future__ import annotations

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.analyzer import analyze_stock
from app.services.rules_doc import load_520_document, load_rules_document

app = FastAPI(title="交易助手网站")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/rules", response_class=HTMLResponse)
async def rules(request: Request):
    document = load_rules_document()
    return templates.TemplateResponse(
        request,
        "rules.html",
        {"document": document, "page_label": "交易系统准则"},
    )


@app.get("/strategy/520", response_class=HTMLResponse)
async def strategy_520(request: Request):
    document = load_520_document()
    return templates.TemplateResponse(
        request,
        "rules.html",
        {"document": document, "page_label": "520战法详解"},
    )


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, code: str = Form(...)):
    try:
        result = analyze_stock(code)
        return templates.TemplateResponse(request, "result.html", {"result": result, "error": None})
    except Exception as exc:
        return templates.TemplateResponse(request, "result.html", {"result": None, "error": str(exc)})
