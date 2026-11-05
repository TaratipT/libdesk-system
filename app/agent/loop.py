import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from app.config import get_openai_client, get_async_openai_client, MODEL_NAME
from app.agent.tools import ALLOWLIST_TOOLS, OPENAI_TOOLS_SPEC
from app.schemas import AgentResponse

SYSTEM_PROMPT = """คุณคือผู้ช่วยระบบบริการและระเบียบห้องสมุด (Library & Policy System) ของสถาบัน
หน้าที่ของคุณคือให้บริการข้อมูลระเบียบ กฎเกณฑ์ สิทธิการยืม-คืน การคำนวณค่าปรับ ค้นหาตำแหน่งหนังสือ และตรวจสอบสถานะ/ความจุ/อุปกรณ์ของห้องค้นคว้ากลุ่มหรือห้องสัมมนาอย่างถูกต้อง เป็นมิตร และสุภาพ

ข้อกำหนด:
1. หากคำถามเกี่ยวกับระเบียบ ให้ใช้ `search_regulations` เสมอ และระบุเลขอ้างอิงหมวด/ข้อ (Citations)
2. หากผู้ใช้ต้องการทราบข้อมูลสมาชิกหรือประวัติการยืม ให้ใช้ `lookup_member`
3. หากต้องคำนวณค่าปรับ ให้ใช้ `calculate_overdue_fine` เสมอ ห้ามคำนวณตัวเลขเอง
4. หากผู้ใช้ถามหาตำแหน่งหนังสือ ให้ใช้ `search_book_location`
5. หากผู้ใช้ถามเกี่ยวกับห้องค้นคว้ากลุ่ม ห้องสัมมนากลุ่ม ความจุ จำนวนคนที่รองรับ อุปกรณ์ หรือตรวจสอบว่าห้องว่างหรือไม่ ให้เรียกใช้ `check_study_rooms` เสมอ แล้วนำข้อมูลของห้องนั้นมาตอบผู้ใช้ให้ครบถ้วน
6. หากเป็นคำถามนอกขอบเขตห้องสมุด ให้ตอบปฏิเสธอย่างสุภาพว่าไม่มีข้อมูล
7. ใช้ภาษาทางการและสุภาพ ห้ามใช้อีโมจิ (Emoji) ทุกชนิดโดยเด็ดขาด
"""

def run_agent_loop(
    user_message: str, 
    member_id: Optional[str] = None,
    max_turns: int = 5
) -> AgentResponse:
    client = get_openai_client()

    full_user_content = user_message
    if member_id:
        full_user_content = f"[รหัสสมาชิก: {member_id}]\n{user_message}"

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": full_user_content}
    ]

    tools_used: List[str] = []
    collected_citations: List[str] = []
    last_action_data: Optional[Dict[str, Any]] = None

    for turn in range(max_turns):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=OPENAI_TOOLS_SPEC,
            tool_choice="auto",
            temperature=0.0
        )

        choice = response.choices[0]
        msg = choice.message

        # stop condition 1: ได้คำตอบแล้ว ไม่เรียก tool ต่อ
        if not msg.tool_calls:
            final_content = msg.content or ""
            return AgentResponse(
                answer=final_content,
                citations=list(dict.fromkeys(collected_citations)),
                tools_used=list(dict.fromkeys(tools_used)),
                action_data=last_action_data
            )

        # บันทึก assistant message พร้อม tool_calls (content=None ตามสเปกมาตรฐาน)
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in msg.tool_calls
            ]
        })

        # วนลูปประมวลผล tool calls ผ่าน allow-list
        for tool_call in msg.tool_calls:
            tool_name = tool_call.function.name
            tools_used.append(tool_name)

            if tool_name not in ALLOWLIST_TOOLS:
                tool_output_str = json.dumps({"error": f"Tool '{tool_name}' not in allow-list"})
            else:
                try:
                    raw_args = json.loads(tool_call.function.arguments or "{}")
                    tool_func = ALLOWLIST_TOOLS[tool_name]
                    result = tool_func(raw_args)
                    last_action_data = result

                    if "citations" in result and isinstance(result["citations"], list):
                        collected_citations.extend(result["citations"])
                    elif "citation" in result and isinstance(result["citation"], str):
                        collected_citations.append(result["citation"])

                    tool_output_str = json.dumps(result, ensure_ascii=False)
                except Exception as e:
                    tool_output_str = json.dumps({"error": str(e)}, ensure_ascii=False)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": tool_output_str
            })

    # stop condition 2: ครบ max_turns
    return AgentResponse(
        answer="ขออภัย ระบบดำเนินการเกินจำนวนรอบสูงสุดที่กำหนด",
        citations=list(dict.fromkeys(collected_citations)),
        tools_used=list(dict.fromkeys(tools_used)),
        action_data=last_action_data
    )

async def run_agent_loop_stream(
    user_message: str,
    member_id: Optional[str] = None,
    max_turns: int = 5
) -> AsyncGenerator[str, None]:
    client = get_async_openai_client()

    full_user_content = user_message
    if member_id:
        full_user_content = f"[รหัสสมาชิก: {member_id}]\n{user_message}"

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": full_user_content}
    ]

    tools_used: List[str] = []
    collected_citations: List[str] = []
    last_action_data: Optional[Dict[str, Any]] = None

    for turn in range(max_turns):
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=OPENAI_TOOLS_SPEC,
            tool_choice="auto",
            temperature=0.0
        )

        choice = response.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            final_content = msg.content or ""
            # สตรีมคำตอบออกมาเป็นชิ้นส่วน (Typewriter stream)
            chunk_size = 4
            for i in range(0, len(final_content), chunk_size):
                tok = final_content[i:i+chunk_size]
                yield f"data: {json.dumps({'type': 'token', 'content': tok}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.012)

            yield f"data: {json.dumps({'type': 'metadata', 'citations': list(dict.fromkeys(collected_citations)), 'tools_used': list(dict.fromkeys(tools_used)), 'action_data': last_action_data}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            return

        # บันทึก assistant message พร้อม tool_calls (content=None ตามสเปกมาตรฐาน)
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in msg.tool_calls
            ]
        })

        for tool_call in msg.tool_calls:
            tool_name = tool_call.function.name
            tools_used.append(tool_name)

            yield f"data: {json.dumps({'type': 'status', 'content': f'ระบบกำลังเรียกใช้: {tool_name}'}, ensure_ascii=False)}\n\n"

            if tool_name not in ALLOWLIST_TOOLS:
                tool_output_str = json.dumps({"error": f"Tool '{tool_name}' not in allow-list"})
            else:
                try:
                    raw_args = json.loads(tool_call.function.arguments or "{}")
                    tool_func = ALLOWLIST_TOOLS[tool_name]
                    result = tool_func(raw_args)
                    last_action_data = result

                    if "citations" in result and isinstance(result["citations"], list):
                        collected_citations.extend(result["citations"])
                    elif "citation" in result and isinstance(result["citation"], str):
                        collected_citations.append(result["citation"])

                    tool_output_str = json.dumps(result, ensure_ascii=False)
                except Exception as e:
                    tool_output_str = json.dumps({"error": str(e)}, ensure_ascii=False)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": tool_output_str
            })

    yield f"data: {json.dumps({'type': 'token', 'content': 'ขออภัย ระบบดำเนินการเกินจำนวนรอบสูงสุดที่กำหนด'}, ensure_ascii=False)}\n\n"
    yield f"data: {json.dumps({'type': 'metadata', 'citations': list(dict.fromkeys(collected_citations)), 'tools_used': list(dict.fromkeys(tools_used)), 'action_data': last_action_data}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"


