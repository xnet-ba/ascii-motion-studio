from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from core.security import verify_token
from storage import db

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    settings: dict = {}
    source_type: Optional[str] = None
    source_path: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    settings: Optional[dict] = None


@router.get("/projects")
async def list_projects(token: str = Depends(verify_token)):
    return {"projects": db.list_projects()}


@router.post("/projects")
async def create_project(payload: ProjectCreate, token: str = Depends(verify_token)):
    pid = db.create_project(payload.name, payload.settings, payload.source_type, payload.source_path)
    return {"project_id": pid}


@router.get("/projects/{project_id}")
async def get_project(project_id: int, token: str = Depends(verify_token)):
    p = db.get_project(project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    return p


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int, token: str = Depends(verify_token)):
    if not db.delete_project(project_id):
        raise HTTPException(404, "Project not found")
    return {"deleted": True}
