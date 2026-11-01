from typing import Dict, Any, List, Optional

# mock ข้อมูลสมาชิก
MEMBERS_DB: Dict[str, Dict[str, Any]] = {
    "STD6501": {
        "member_id": "STD6501",
        "name": "นายสมชาย ใจดี",
        "role": "undergraduate",
        "role_th": "นักศึกษาปริญญาตรี",
        "faculty": "วิศวกรรมศาสตร์",
        "fine_balance": 0.0,
        "borrowed_books": [
            {
                "book_id": "BK-101",
                "title": "Python Data Science Handbook",
                "borrowed_date": "2026-10-15",
                "due_date": "2026-10-29",
                "days_overdue": 3,
                "book_type": "general"
            },
            {
                "book_id": "BK-102",
                "title": "Clean Code",
                "borrowed_date": "2026-10-25",
                "due_date": "2026-11-08",
                "days_overdue": 0,
                "book_type": "general"
            }
        ]
    },
    "STD6502": {
        "member_id": "STD6502",
        "name": "นางสาววิภา สุขุม",
        "role": "graduate",
        "role_th": "นักศึกษาปริญญาโท",
        "faculty": "เทคโนโลยีสารสนเทศ",
        "fine_balance": 45.0,
        "borrowed_books": [
            {
                "book_id": "BK-105",
                "title": "Designing Data-Intensive Applications",
                "borrowed_date": "2026-09-20",
                "due_date": "2026-10-20",
                "days_overdue": 12,
                "book_type": "general"
            }
        ]
    },
    "PRF1001": {
        "member_id": "PRF1001",
        "name": "ผศ. ดร. กิตติภพ ธนะสาร",
        "role": "faculty",
        "role_th": "อาจารย์ประจำ",
        "faculty": "วิทยาศาสตร์",
        "fine_balance": 0.0,
        "borrowed_books": [
            {
                "book_id": "BK-108",
                "title": "Artificial Intelligence: A Modern Approach",
                "borrowed_date": "2026-08-15",
                "due_date": "2026-11-15",
                "days_overdue": 0,
                "book_type": "general"
            }
        ]
    }
}

# mock แคตตาล็อกหนังสือ
CATALOG_DB: List[Dict[str, Any]] = [
    {
        "book_id": "BK-101",
        "title": "Python Data Science Handbook",
        "author": "Jake VanderPlas",
        "call_number": "QA76.73.P98 V36 2023",
        "category": "Computer Science",
        "location": "ชั้น 3 โซน A ตู้ A-04",
        "status": "ถูกยืมอยู่",
        "book_type": "general",
        "cover_price": 850.0
    },
    {
        "book_id": "BK-102",
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "call_number": "QA76.76.C64 M37 2008",
        "category": "Software Engineering",
        "location": "ชั้น 3 โซน A ตู้ A-02",
        "status": "ถูกยืมอยู่",
        "book_type": "general",
        "cover_price": 950.0
    },
    {
        "book_id": "BK-103",
        "title": "Introduction to Algorithms (CLRS)",
        "author": "Thomas H. Cormen et al.",
        "call_number": "QA76.6 .I585 2022",
        "category": "Algorithms",
        "location": "ชั้น 2 เคาน์เตอร์หนังสือสำรอง",
        "status": "พร้อมให้บริการ (หนังสือสำรอง)",
        "book_type": "reserve",
        "cover_price": 2200.0
    },
    {
        "book_id": "BK-104",
        "title": "พจนานุกรมฉบับราชบัณฑิตยสถาน พ.ศ. 2554",
        "author": "ราชบัณฑิตยสถาน",
        "call_number": "REF PL4187 .R34 2554",
        "category": "Reference",
        "location": "ชั้น 1 มุมหนังสืออ้างอิง ตู้ R-01",
        "status": "ไม่อนุญาตให้ยืมออกนอกห้องสมุด",
        "book_type": "reference",
        "cover_price": 1500.0
    },
    {
        "book_id": "BK-105",
        "title": "Designing Data-Intensive Applications",
        "author": "Martin Kleppmann",
        "call_number": "QA76.9.D3 K58 2017",
        "category": "Distributed Systems",
        "location": "ชั้น 3 โซน B ตู้ B-01",
        "status": "ถูกยืมอยู่",
        "book_type": "general",
        "cover_price": 1250.0
    },
    {
        "book_id": "BK-106",
        "title": "Database System Concepts (7th Edition)",
        "author": "Abraham Silberschatz",
        "call_number": "QA76.9.D3 S56 2020",
        "category": "Database",
        "location": "ชั้น 3 โซน B ตู้ B-03",
        "status": "พร้อมให้บริการ",
        "book_type": "general",
        "cover_price": 1400.0
    }
]

# mock ห้องค้นคว้ากลุ่ม
ROOMS_DB: List[Dict[str, Any]] = [
    {
        "room_id": "GSR-201",
        "name": "ห้องค้นคว้ากลุ่ม 201 (ขนาดเล็ก)",
        "capacity": "4-6 คน (ขั้นต่ำ 3 คน)",
        "equipment": "Smart TV 55 นิ้ว, กระดานไวท์บอร์ด, ปลั๊กไฟ 6 จุด",
        "status": "ว่าง"
    },
    {
        "room_id": "GSR-202",
        "name": "ห้องค้นคว้ากลุ่ม 202 (ขนาดเล็ก)",
        "capacity": "4-6 คน (ขั้นต่ำ 3 คน)",
        "equipment": "Smart TV 55 นิ้ว, กระดานไวท์บอร์ด, ปลั๊กไฟ 6 จุด",
        "status": "มีการจอง (13:00 - 16:00)"
    },
    {
        "room_id": "GSR-301",
        "name": "ห้องสัมมนากลุ่ม 301 (ขนาดใหญ่)",
        "capacity": "7-12 คน (ขั้นต่ำ 5 คน)",
        "equipment": "Projector 4K, กระดานกระจก, ระบบประชุมทางไกล",
        "status": "ว่าง"
    }
]

def get_member(member_id: str) -> Optional[Dict[str, Any]]:
    return MEMBERS_DB.get(member_id.strip().upper())

def search_catalog(query: str) -> List[Dict[str, Any]]:
    q = query.strip().lower()
    results = []
    for book in CATALOG_DB:
        if (q in book["title"].lower() or 
            q in book["author"].lower() or 
            q in book["call_number"].lower() or 
            q in book["category"].lower()):
            results.append(book)
    return results

def get_all_study_rooms() -> List[Dict[str, Any]]:
    return ROOMS_DB
