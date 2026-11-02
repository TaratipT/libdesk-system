import json
from typing import List, Dict, Any, Optional
from app.config import get_openai_client, MODEL_NAME
from app.agent.tools import ALLOWLIST_TOOLS, OPENAI_TOOLS_SPEC
from app.schemas import AgentResponse

SYSTEM_PROMPT = """คุณคือผู้ช่วยระบบบริการและระเบียบห้องสมุด (Library & Policy System) ของสถาบัน
หน้าที่ของคุณคือให้บริการข้อมูลระเบียบ กฎเกณฑ์ สิทธิการยืม-คืน การคำนวณค่าปรับ และค้นหาตำแหน่งหนังสือในห้องสมุดอย่างถูกต้อง เป็นมิตร และสุภาพ

ข้อกำหนด:
1. หากคำถามเกี่ยวกับระเบียบ ให้ใช้ `search_regulations` เสมอ และระบุเลขอ้างอิงหมวด/ข้อ (Citations)
2. หากผู้ใช้ต้องการทราบข้อมูลสมาชิกหรือประวัติการยืม ให้ใช้ `lookup_member`
3. หากต้องคำนวณค่าปรับ ให้ใช้ `calculate_overdue_fine` เสมอ ห้ามคำนวณตัวเลขเอง
4. หากผู้ใช้ถามหาตำแหน่งหนังสือ ให้ใช้ `search_book_location`
5. หากเป็นคำถามนอกขอบเขตห้องสมุด ให้ตอบปฏิเสธอย่างสุภาพว่าไม่มีข้อมูล
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

        messages.append(msg)

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

