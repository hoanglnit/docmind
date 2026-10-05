from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.scenario import Scenario
from ..schemas.scenario import ScenarioCreate, ScenarioUpdate, ScenarioOut

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioOut])
def list_scenarios(db: Session = Depends(get_db)):
    return db.query(Scenario).order_by(Scenario.created_at.desc()).all()


@router.post("", response_model=ScenarioOut, status_code=201)
def create_scenario(body: ScenarioCreate, db: Session = Depends(get_db)):
    if body.is_default:
        db.query(Scenario).update({"is_default": False})
    scenario = Scenario(**body.model_dump())
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.get("/{scenario_id}", response_model=ScenarioOut)
def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    s = db.get(Scenario, scenario_id)
    if not s:
        raise HTTPException(404, "Không tìm thấy kịch bản")
    return s


@router.put("/{scenario_id}", response_model=ScenarioOut)
def update_scenario(scenario_id: str, body: ScenarioUpdate, db: Session = Depends(get_db)):
    s = db.get(Scenario, scenario_id)
    if not s:
        raise HTTPException(404, "Không tìm thấy kịch bản")
    if body.is_default:
        db.query(Scenario).filter(Scenario.id != scenario_id).update({"is_default": False})
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(s, field, value)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{scenario_id}", status_code=204)
def delete_scenario(scenario_id: str, db: Session = Depends(get_db)):
    s = db.get(Scenario, scenario_id)
    if not s:
        raise HTTPException(404, "Không tìm thấy kịch bản")
    db.delete(s)
    db.commit()
