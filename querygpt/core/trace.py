from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from uuid import uuid4


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: str
    tracestep_id: str
    
    def to_json(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments)
            }
        }


class TraceStep(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    trace_id: Optional[str] = None
    step_number: Optional[int] = None
    step_type: str
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Action step fields
    model_input: Optional[str] = None
    model_output: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_calls_json: Optional[str] = None
    observations: Optional[str] = None
    error: Optional[str] = None
    action_output: Optional[Dict[str, Any] | str] = None
    
    # Planning step fields
    plan: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary suitable for database storage"""
        result = self.model_dump(exclude_none=True, warnings=False)
        
        if self.tool_calls:
            result["tool_calls"] = json.dumps([tc.to_json() for tc in self.tool_calls])
            
        if self.action_output and isinstance(self.action_output, dict):
            result["action_output"] = json.dumps(self.action_output)
            
        return result


class Trace(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    task: str
    enhanced_task: Optional[str] = None
    system_prompt: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    final_answer: Optional[str] = None
    total_steps: Optional[int] = None
    steps: List[TraceStep] = Field(default_factory=list)
    
    def add_step(self, step: TraceStep) -> TraceStep:
        """Add a step to the trace and set its step number"""
        step.trace_id = self.id
        if step.step_number is None:
            step.step_number = len(self.steps) + 1
        self.steps.append(step)
        return step
    
    def finish(self, final_answer: str) -> "Trace":
        """Mark the trace as complete with the final answer"""
        self.end_time = datetime.now()
        self.final_answer = final_answer
        if self.start_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.total_steps = len(self.steps)
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary suitable for database storage"""
        result = self.model_dump(exclude={"steps"}, exclude_none=True, warnings=False)
        
        if self.steps:
            result["steps"] = [step.to_dict() for step in self.steps]
        return result