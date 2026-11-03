// LibDesk: Library Service & Regulation Circulation Desk - Client Logic (with SSE Streaming)

// ตัวแปรเก็บสถานะบัญชีสมาชิกปัจจุบัน (เริ่มต้นด้วย Guest)
let currentMemberId = null;

document.addEventListener("DOMContentLoaded", () => {
    renderGuestCard();
    loadStudyRooms();

    // ปิด Modal เมื่อกดปุ่ม Escape
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeLoginModal();
        }
    });
});

// เปิดหน้าต่าง Modal เข้าสู่ระบบ
function openLoginModal() {
    const modal = document.getElementById("login-modal");
    if (modal) {
        modal.classList.remove("hidden");
    }
}

// ปิดหน้าต่าง Modal เข้าสู่ระบบ
function closeLoginModal() {
    const modal = document.getElementById("login-modal");
    if (modal) {
        modal.classList.add("hidden");
    }
}

// ปิด Modal เมื่อคลิกที่พื้นหลังมืด
function closeLoginModalOnBackdrop(e) {
    if (e.target.id === "login-modal") {
        closeLoginModal();
    }
}

// เข้าสู่ระบบด้วยบัญชีสมาชิกที่เลือก
async function loginAs(memberId) {
    try {
        const res = await fetch(`/api/member/${memberId}`);
        if (!res.ok) throw new Error("ไม่พบข้อมูลสมาชิกในระบบ");
        const data = await res.json();

        currentMemberId = data.member_id;

        // อัปเดตการ์ดข้อมูลผู้ใช้บริการฝั่งซ้าย
        renderMemberCard(data);

        // อัปเดตแถบส่วนหัว (Header) เป็นโหมดสมาชิก
        const guestState = document.getElementById("guest-header-state");
        const memberState = document.getElementById("member-header-state");
        const headerName = document.getElementById("header-user-name");
        const headerId = document.getElementById("header-user-id");

        if (headerName) headerName.textContent = data.name;
        if (headerId) headerId.textContent = data.member_id;

        if (guestState) guestState.classList.add("hidden");
        if (memberState) memberState.classList.remove("hidden");

        // ปิดหน้าต่าง Modal
        closeLoginModal();
    } catch (err) {
        alert("เข้าสู่ระบบไม่สำเร็จ: " + err.message);
    }
}

// ออกจากระบบ สลับกลับเป็น Guest Mode
function logout() {
    currentMemberId = null;

    // อัปเดตการ์ดข้อมูลฝั่งซ้ายกลับเป็น Guest
    renderGuestCard();

    // อัปเดตแถบส่วนหัว (Header) เป็นโหมด Guest
    const guestState = document.getElementById("guest-header-state");
    const memberState = document.getElementById("member-header-state");

    if (memberState) memberState.classList.add("hidden");
    if (guestState) guestState.classList.remove("hidden");
}

// แสดงข้อมูลบุคคลทั่วไป (Guest)
function renderGuestCard() {
    document.getElementById("card-member-id").textContent = "-";
    document.getElementById("card-member-name").textContent = "บุคคลทั่วไป (Guest)";
    document.getElementById("card-member-faculty").textContent = "บุคคลภายนอก";
    document.getElementById("member-role-badge").textContent = "ผู้ใช้บริการทั่วไป";

    const fineBox = document.getElementById("fine-box");
    const fineEl = document.getElementById("card-fine-balance");
    const fineDesc = document.getElementById("fine-desc");
    
    fineBox.classList.remove("has-fine");
    fineEl.textContent = "0.00 บาท";
    fineEl.className = "fine-value tag-success";
    fineDesc.textContent = "สถานะบุคคลทั่วไป ไม่มีภาระผูกพันในระบบ";

    const booksList = document.getElementById("borrowed-books-list");
    booksList.innerHTML = `<li class="item-card" style="color: var(--text-muted); text-align: center; font-size: 0.84rem;">ไม่มีรายการทรัพยากรค้างส่งในระบบ</li>`;
}

// แสดงข้อมูลบัตรสมาชิก
function renderMemberCard(data) {
    document.getElementById("card-member-id").textContent = data.member_id;
    document.getElementById("card-member-name").textContent = data.name;
    document.getElementById("card-member-faculty").textContent = data.faculty;
    document.getElementById("member-role-badge").textContent = data.role_th;

    const fineBox = document.getElementById("fine-box");
    const fineEl = document.getElementById("card-fine-balance");
    const fineDesc = document.getElementById("fine-desc");

    fineEl.textContent = `${Number(data.fine_balance).toFixed(2)} บาท`;
    if (data.fine_balance > 0) {
        fineBox.classList.add("has-fine");
        fineEl.className = "fine-value tag-danger";
        fineDesc.textContent = "มียอดค่าปรับค้างชำระ กรุณาติดต่อชำระที่เคาน์เตอร์การเงิน";
    } else {
        fineBox.classList.remove("has-fine");
        fineEl.className = "fine-value tag-success";
        fineDesc.textContent = "สถานะบัญชีปกติ ไม่มีภาระหนี้สินค้างชำระ";
    }

    const booksList = document.getElementById("borrowed-books-list");
    booksList.innerHTML = "";

    if (!data.borrowed_books || data.borrowed_books.length === 0) {
        booksList.innerHTML = `<li class="item-card" style="color: var(--text-muted); text-align: center; font-size: 0.85rem;">ไม่มีรายการทรัพยากรที่ยืมค้างส่ง</li>`;
        return;
    }

    data.borrowed_books.forEach(b => {
        const isOverdue = b.days_overdue > 0;
        const statusBadge = isOverdue 
            ? `<span class="tag-danger">เกินกำหนด ${b.days_overdue} วัน</span>` 
            : `<span class="tag-success">กำหนดส่ง: ${b.due_date}</span>`;

        const li = document.createElement("li");
        li.className = "item-card";
        li.innerHTML = `
            <div class="item-title">${b.title}</div>
            <div class="item-meta">
                <span>ยืมเมื่อ: ${b.borrowed_date}</span>
                ${statusBadge}
            </div>
        `;
        booksList.appendChild(li);
    });
}

// โหลดสถานะห้องค้นคว้ากลุ่ม
async function loadStudyRooms() {
    try {
        const res = await fetch("/api/study-rooms");
        if (!res.ok) return;
        const rooms = await res.json();
        const container = document.getElementById("room-status-list");
        container.innerHTML = "";

        rooms.forEach(r => {
            const isAvail = r.status === "ว่าง";
            const badgeClass = isAvail ? "tag-success" : "tag-danger";
            const li = document.createElement("div");
            li.className = "item-card";
            li.innerHTML = `
                <div class="item-header-row">
                    <span class="item-title">${r.name}</span>
                    <span class="${badgeClass}">${r.status}</span>
                </div>
                <div class="item-sub-desc">ความจุ: ${r.capacity}</div>
            `;
            container.appendChild(li);
        });
    } catch (err) {
        console.error("Error loading rooms:", err);
    }
}

// ส่งข้อความสอบถามด้วยระบบ SSE Streaming (Lecture 4 Standard)
async function submitQuery(e) {
    if (e) e.preventDefault();
    const input = document.getElementById("query-input");
    const query = input.value.trim();
    if (!query) return;

    const memberId = currentMemberId;

    const submitBtn = document.getElementById("submit-btn");
    const loadingCard = document.getElementById("loading-card");
    const resultContainer = document.getElementById("result-container");
    const welcomeCard = document.getElementById("welcome-card");
    const answerText = document.getElementById("answer-text");
    const processTag = document.getElementById("system-process-tag");
    const citationsList = document.getElementById("citations-list");
    const actionBox = document.getElementById("action-data-box");
    const loadingTitle = document.querySelector("#loading-card .loading-title");

    submitBtn.disabled = true;
    if (welcomeCard) welcomeCard.classList.add("hidden");
    loadingCard.classList.remove("hidden");
    if (loadingTitle) loadingTitle.textContent = "กำลังสืบค้นข้อบังคับและประมวลผลข้อมูล...";
    resultContainer.classList.add("hidden");

    // ล้างข้อความผลลัพธ์รอบก่อนหน้า
    answerText.textContent = "";
    processTag.textContent = "ระบบงาน: ศูนย์บริการสารสนเทศทั่วไป";
    citationsList.innerHTML = "";
    actionBox.innerHTML = "";
    actionBox.classList.add("hidden");

    try {
        const res = await fetch("/api/chat/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: query,
                member_id: memberId
            })
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || "เกิดข้อผิดพลาดในการประมวลผลข้อมูล");
        }

        // Lecture 4: อ่าน SSE Stream ผ่าน ReadableStream (TextDecoderStream)
        const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
        let buffer = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += value;
            const events = buffer.split("\n\n");
            buffer = events.pop();

            for (const ev of events) {
                if (ev.startsWith("data: ")) {
                    const rawData = ev.slice(6).trim();
                    if (rawData === "[DONE]") {
                        break;
                    }

                    try {
                        const payload = JSON.parse(rawData);

                        if (payload.type === "status") {
                            if (loadingTitle) loadingTitle.textContent = payload.content;
                        } else if (payload.type === "token") {
                            if (!loadingCard.classList.contains("hidden")) {
                                loadingCard.classList.add("hidden");
                                resultContainer.classList.remove("hidden");
                            }
                            answerText.textContent += payload.content;
                        } else if (payload.type === "metadata") {
                            renderMetadata(payload);
                        }
                    } catch (errParse) {
                        console.warn("SSE frame error:", errParse);
                    }
                }
            }
        }

        input.value = "";
    } catch (err) {
        alert("ข้อผิดพลาด: " + err.message);
        if (welcomeCard && resultContainer.classList.contains("hidden")) {
            welcomeCard.classList.remove("hidden");
        }
    } finally {
        submitBtn.disabled = false;
        loadingCard.classList.add("hidden");
        if (answerText.textContent.trim()) {
            resultContainer.classList.remove("hidden");
        }
    }
}

// แปลงชื่อ Tool ทางเทคนิคเป็นชื่องานบริการทางการ
function mapToolToThai(toolName) {
    const map = {
        "calculate_overdue_fine": "ระบบคำนวณอัตราค่าปรับตามระเบียบ",
        "lookup_member": "ระบบตรวจสอบฐานข้อมูลทะเบียนสมาชิก",
        "search_regulations": "ระบบสืบค้นหมวดข้อบังคับสถาบัน",
        "search_book_location": "ระบบสืบค้นตำแหน่งคลังทรัพยากรสารสนเทศ",
        "check_study_rooms": "ระบบตรวจสอบสถานะห้องค้นคว้ากลุ่ม"
    };
    return map[toolName] || toolName;
}

// เรนเดอร์ Citations และ Action Data เมื่อสตรีมเสร็จสิ้น
function renderMetadata(data) {
    const processTag = document.getElementById("system-process-tag");
    const citationsList = document.getElementById("citations-list");
    const actionBox = document.getElementById("action-data-box");

    // แสดงระบบงานที่ประมวลผล
    if (data.tools_used && data.tools_used.length > 0) {
        const thaiNames = data.tools_used.map(mapToolToThai).join(", ");
        processTag.textContent = `ระบบงานที่ตรวจสอบ: ${thaiNames}`;
    } else {
        processTag.textContent = "ระบบงาน: ศูนย์บริการสารสนเทศทั่วไป";
    }

    // ป้ายข้อบังคับที่ใช้อ้างอิง
    citationsList.innerHTML = "";
    if (data.citations && data.citations.length > 0) {
        data.citations.forEach(c => {
            const span = document.createElement("span");
            span.className = "citation-pill";
            span.textContent = c;
            citationsList.appendChild(span);
        });
    } else {
        citationsList.innerHTML = `<span style="font-size: 0.85rem; color: var(--text-muted);">- ไม่พบข้อบังคับเฉพาะเจาะจงที่ต้องใช้อ้างอิง -</span>`;
    }

    // ตารางข้อมูลทางการเพิ่มเติม
    actionBox.innerHTML = "";
    if (data.action_data) {
        const ad = data.action_data;

        if ("fine_amount" in ad) {
            actionBox.classList.remove("hidden");
            actionBox.innerHTML = `
                <div style="font-weight: 700; color: var(--navy-900); margin-bottom: 8px;">ใบสรุปการประเมินค่าปรับตามระเบียบ</div>
                <table class="official-table">
                    <tr><th style="width: 32%;">ประเภททรัพยากร</th><td>${ad.book_type === "general" ? "หนังสือทั่วไป" : ad.book_type}</td></tr>
                    <tr><th>หลักเกณฑ์การคำนวณ</th><td>${ad.formula_description || "-"}</td></tr>
                    <tr><th>ยอดค่าปรับสุทธิ</th><td><strong style="color: var(--danger-text); font-size: 1.05rem;">${Number(ad.fine_amount).toFixed(2)} บาท</strong></td></tr>
                </table>
            `;
        } else if (ad.books && ad.books.length > 0) {
            actionBox.classList.remove("hidden");
            let rows = ad.books.map(b => {
                const isAvail = b.status === "พร้อมให้บริการ";
                const badgeClass = isAvail ? "tag-success" : "tag-danger";
                return `
                <tr>
                    <td><strong>${b.title}</strong></td>
                    <td><span class="font-mono" style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.82rem;">${b.call_number}</span></td>
                    <td>${b.location}</td>
                    <td><span class="${badgeClass}">[${b.status}]</span></td>
                </tr>
            `;
            }).join("");

            actionBox.innerHTML = `
                <div style="font-weight: 700; color: var(--navy-900); margin-bottom: 8px;">รายการทรัพยากรสารสนเทศในคลัง (พบ ${ad.books.length} รายการ)</div>
                <table class="official-table">
                    <thead>
                        <tr><th>ชื่อเรื่อง</th><th>เลขเรียกหนังสือ</th><th>สถานที่จัดเก็บ</th><th>สถานะความพร้อม</th></tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            `;
        } else {
            actionBox.classList.add("hidden");
        }
    } else {
        actionBox.classList.add("hidden");
    }
}

// ตัวช่วยใส่คำถามจาก Quick Topic Button
function setQuery(text) {
    const input = document.getElementById("query-input");
    input.value = text;
    submitQuery();
}
