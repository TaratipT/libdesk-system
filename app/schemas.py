from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

# schemas สำหรับ input ของ tools
class SearchRegulationsInput(BaseModel):
    query: str = Field(..., description="คำค้นหาระเบียบห้องสมุด เช่น 'ค่าปรับส่งช้า', 'สิทธิการยืม'")

class LookupMemberInput(BaseModel):
    member_id: str = Field(..., description="รหัสสมาชิก เช่น STD6501, STD6502, PRF1001")

class CalculateOverdueFineInput(BaseModel):
    book_type: Literal["general", "reserve", "device"] = Field(
        default="general", 
        description="ประเภทหนังสือ: general (ทั่วไป), reserve (สำรอง), device (อุปกรณ์ไอที)"
    )
    days_overdue: int = Field(default=0, ge=0, description="จำนวนวันที่เกินกำหนด (หนังสือทั่วไป)")
    hours_overdue: int = Field(default=0, ge=0, description="จำนวนชั่วโมงที่เกินกำหนด (หนังสือสำรอง/อุปกรณ์)")

class SearchBookLocationInput(BaseModel):
    query: str = Field(..., description="ชื่อหนังสือ ผู้แต่ง หรือเลขเรียกหนังสือ")

class CheckStudyRoomsInput(BaseModel):
    room_query: Optional[str] = Field(default=None, description="ชื่อหรือหมายเลขห้องค้นคว้า เช่น '201', '301', 'ขนาดเล็ก', 'ขนาดใหญ่'")

# schemas สำหรับผลลัพธ์ของ agent
class AgentResponse(BaseModel):
    answer: str
    citations: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    action_data: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    member_id: Optional[str] = None

