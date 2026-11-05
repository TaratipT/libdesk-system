import json
from typing import Dict, Any, List
from app.schemas import (
    SearchRegulationsInput,
    LookupMemberInput,
    CalculateOverdueFineInput,
    SearchBookLocationInput,
    CheckStudyRoomsInput
)
from app.rag.retriever import retrieve_regulations
from app.database import get_member, search_catalog, get_all_study_rooms

# ฟังก์ชันการทำงานจริงของแต่ละ Tool
def tool_search_regulations(params: Dict[str, Any]) -> Dict[str, Any]:
    validated = SearchRegulationsInput(**params)
    retrieval_res = retrieve_regulations(query=validated.query, top_k=3)
    return {
        "found_count": len(retrieval_res["results"]),
        "citations": retrieval_res["citations"],
        "context": retrieval_res["context"]
    }

def tool_lookup_member(params: Dict[str, Any]) -> Dict[str, Any]:
    validated = LookupMemberInput(**params)
    member = get_member(validated.member_id)
    if not member:
        return {
            "status": "not_found",
            "message": f"ไม่พบข้อมูลสมาชิก: {validated.member_id}"
        }
    return {
        "status": "success",
        "member_data": member
    }

def tool_calculate_overdue_fine(params: Dict[str, Any]) -> Dict[str, Any]:
    validated = CalculateOverdueFineInput(**params)
    book_type = validated.book_type
    days = validated.days_overdue
    hours = validated.hours_overdue

    fine_amount = 0.0
    rate_desc = ""

    if book_type == "general":
        daily_rate = 5.0
        calculated = days * daily_rate
        fine_amount = min(calculated, 500.0)
        rate_desc = f"อัตราวันละ {daily_rate:.0f} บาท (เกิน {days} วัน, เพดานสูงสุด 500 บาทต่อเล่ม)"
    elif book_type == "reserve":
        hourly_rate = 10.0
        fine_amount = hours * hourly_rate
        rate_desc = f"อัตราชั่วโมงละ {hourly_rate:.0f} บาท (เกิน {hours} ชั่วโมง)"
    elif book_type == "device":
        hourly_rate = 50.0
        fine_amount = hours * hourly_rate
        rate_desc = f"อัตราอุปกรณ์ชั่วโมงละ {hourly_rate:.0f} บาท (เกิน {hours} ชั่วโมง)"

    return {
        "book_type": book_type,
        "days_overdue": days,
        "hours_overdue": hours,
        "fine_amount": fine_amount,
        "formula_description": rate_desc,
        "citation": "ระเบียบห้องสมุด หมวด 4 ข้อ 4.1 และ 4.2"
    }

def tool_search_book_location(params: Dict[str, Any]) -> Dict[str, Any]:
    validated = SearchBookLocationInput(**params)
    matches = search_catalog(validated.query)
    return {
        "query": validated.query,
        "found_count": len(matches),
        "books": matches
    }

def tool_check_study_rooms(params: Dict[str, Any]) -> Dict[str, Any]:
    validated = CheckStudyRoomsInput(**params) if params else CheckStudyRoomsInput()
    rooms = get_all_study_rooms()
    if validated.room_query:
        q = validated.room_query.strip().lower()
        matched = [r for r in rooms if q in r["name"].lower() or q in r["room_id"].lower() or q in r["capacity"].lower()]
        if matched:
            return {
                "total_rooms": len(matched),
                "rooms": matched
            }
    return {
        "total_rooms": len(rooms),
        "rooms": rooms
    }

# allow-list สำหรับความปลอดภัย
ALLOWLIST_TOOLS = {
    "search_regulations": tool_search_regulations,
    "lookup_member": tool_lookup_member,
    "calculate_overdue_fine": tool_calculate_overdue_fine,
    "search_book_location": tool_search_book_location,
    "check_study_rooms": tool_check_study_rooms,
}

# specification สำหรับ OpenAI Function Calling
OPENAI_TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "search_regulations",
            "description": "ค้นหาระเบียบและข้อบังคับห้องสมุดตามคำค้นหา",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "ข้อความค้นหาระเบียบ เช่น 'สิทธิการยืม ป.ตรี', 'เวลาเปิดช่วงสอบ'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_member",
            "description": "ตรวจสอบข้อมูลสมาชิก รายการหนังสือที่ยืมอยู่ และวันครบกำหนดส่ง",
            "parameters": {
                "type": "object",
                "properties": {
                    "member_id": {
                        "type": "string",
                        "description": "รหัสสมาชิก เช่น 'STD6501', 'STD6502'"
                    }
                },
                "required": ["member_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_overdue_fine",
            "description": "คำนวณยอดเงินค่าปรับเกินกำหนดส่งตามสูตรระเบียบห้องสมุด",
            "parameters": {
                "type": "object",
                "properties": {
                    "book_type": {
                        "type": "string",
                        "enum": ["general", "reserve", "device"],
                        "description": "ประเภททรัพยากร: ส่ง 'general' สำหรับหนังสือทั่วไป, 'reserve' สำหรับหนังสือสำรอง, 'device' สำหรับอุปกรณ์ไอที"
                    },
                    "days_overdue": {"type": "integer", "description": "จำนวนวันที่เกินส่ง (หนังสือทั่วไป)"},
                    "hours_overdue": {"type": "integer", "description": "จำนวนชั่วโมงที่เกินส่ง (หนังสือสำรอง)"}
                },
                "required": ["book_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_book_location",
            "description": "ค้นหาตำแหน่งตู้ ชั้นวาง และเลขเรียกหนังสือในแคตตาล็อก",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "ชื่อหนังสือหรือเลขเรียกหนังสือ"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_study_rooms",
            "description": "ตรวจสอบสถานะ ความจุ จำนวนคนที่รองรับ อุปกรณ์ และช่วงเวลาว่างของห้องค้นคว้ากลุ่มและห้องสัมมนากลุ่มทั้งหมด (เมื่อมีคำถามเกี่ยวกับห้องค้นคว้ากลุ่ม ห้องสัมมนา ห้องว่างไหม หรือจุได้กี่คน ให้เรียกฟังก์ชันนี้เสมอ)",
            "parameters": {
                "type": "object",
                "properties": {
                    "room_query": {
                        "type": "string",
                        "description": "ชื่อ หมายเลขห้อง หรือประเภทห้อง เช่น '201', '301', 'ห้องสัมมนา', 'ขนาดเล็ก', 'ขนาดใหญ่' (หากไม่ระบุจะดึงข้อมูลทุกห้อง)"
                    }
                }
            }
        }
    }
]

