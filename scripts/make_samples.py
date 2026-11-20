"""Generate fictitious sample documents (enrollment form + handbook) for testing.

Usage: python scripts/make_samples.py data/samples
All people, organizations and numbers are made up.
"""
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)

SCHOOL = "Maple Ridge Online University"
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Title"], fontSize=20)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], spaceBefore=12)
BODY = ParagraphStyle("B", parent=ss["BodyText"], fontSize=10.5, leading=15)


def kv_table(rows):
    t = Table(rows, colWidths=[2.2 * inch, 4.3 * inch])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# ---------- Enrollment forms ----------
STUDENTS = [
    {
        "slug": "sarah_wilson", "app_id": "MROU-2026-00417", "submitted": "August 14, 2026",
        "name": "Sarah Elizabeth Wilson", "preferred": "Sarah", "dob": "March 9, 2008", "gender": "Female",
        "address": "2418 Birchwood Lane, Springfield, IL 62704", "email": "sarah.wilson2008@example.com",
        "phone": "(217) 555-0166", "prev_school": "Springfield Central High School, Springfield, IL",
        "hs_grad": "May 2026", "major": "Computer Science (B.S.)", "status": "Full-time (12 credits)",
        "courses": "ENGL 101, MATH 151 Calculus I, CSCI 110 Intro to Programming, PSYC 101",
        "ap": "AP Calculus AB (score 4), AP English Language (score 4)", "aid": "Yes (FAFSA submitted)",
        "contacts": [("Primary contact", "Megan Wilson (Mother)", "(217) 555-0193", "megan.wilson@example.com"),
                     ("Secondary contact", "David Wilson (Father)", "(217) 555-0178", "david.wilson@example.com")],
        "other_contact": "Linda Carter (Grandmother), (217) 555-0142",
        "allergies": "Peanuts (carries epinephrine auto-injector)",
        "physician": "Dr. Anita Rao, Springfield Family Health, (217) 555-0110",
        "accommodations": "No", "honors": "Yes - Computer Science",
        "ferpa": "Yes - Megan Wilson, David Wilson", "directory": "No", "photo": "Yes",
    },
    {
        "slug": "marcus_johnson", "app_id": "MROU-2026-00533", "submitted": "August 19, 2026",
        "name": "Marcus Anthony Johnson", "preferred": "Marcus", "dob": "January 22, 2007", "gender": "Male",
        "address": "77 Elm Court, Peoria, IL 61602", "email": "marcus.johnson2007@example.com",
        "phone": "(309) 555-0121", "prev_school": "Peoria Valley High School, Peoria, IL",
        "hs_grad": "May 2025", "major": "Business Administration (B.B.A.)", "status": "Part-time (6 credits)",
        "courses": "BUSN 101 Intro to Business, ACCT 201 Financial Accounting",
        "ap": "None", "aid": "No",
        "contacts": [("Primary contact", "Denise Johnson (Mother)", "(309) 555-0134", "denise.johnson@example.com"),
                     ("Secondary contact", "Robert Johnson (Father)", "(309) 555-0152", "robert.johnson@example.com")],
        "other_contact": "Tanya Brooks (Aunt), (309) 555-0188",
        "allergies": "None known",
        "physician": "Dr. Paul Reyes, Peoria Community Clinic, (309) 555-0177",
        "accommodations": "Yes - extended time on exams", "honors": "No",
        "ferpa": "No", "directory": "Yes", "photo": "No",
    },
    {
        "slug": "kim_wu", "app_id": "MROU-2026-00588", "submitted": "August 22, 2026",
        "name": "Kim Mei Wu", "preferred": "Kim", "dob": "November 3, 2007", "gender": "Female",
        "address": "905 Lakeview Drive, Naperville, IL 60540", "email": "kim.wu2007@example.com",
        "phone": "(630) 555-0148", "prev_school": "Naperville North High School, Naperville, IL",
        "hs_grad": "May 2026", "major": "Data Science (B.S.)", "status": "Full-time (15 credits)",
        "courses": "STAT 201 Intro to Statistics, CSCI 110 Intro to Programming, MATH 151 Calculus I, ENGL 101, ECON 101",
        "ap": "AP Statistics (score 5)", "aid": "Yes (institutional scholarship)",
        "contacts": [("Primary contact", "Helen Wu (Mother)", "(630) 555-0163", "helen.wu@example.com")],
        "other_contact": "None",
        "allergies": "Penicillin (rash)",
        "physician": "Dr. Samir Patel, Naperville Pediatrics, (630) 555-0105",
        "accommodations": "No", "honors": "Yes - Data Science",
        "ferpa": "Yes - Helen Wu", "directory": "No", "photo": "Yes",
    },
]


def enrollment(p):
    doc = SimpleDocTemplate(str(out / f"enrollment_{p['slug']}.pdf"), pagesize=letter,
                            leftMargin=inch, rightMargin=inch, topMargin=0.8 * inch, bottomMargin=0.8 * inch)
    contact_rows = []
    for label, who, phone, email in p["contacts"]:
        contact_rows += [[label, who], ["Phone", phone], ["Email", email]]
    contact_rows.append(["Other contact", p["other_contact"]])
    s = [
        Paragraph(SCHOOL, H1),
        Paragraph("Undergraduate Enrollment Form - Fall 2026", ss["Heading3"]),
        Paragraph(f"Submitted: {p['submitted']} &nbsp;&nbsp; Application ID: {p['app_id']}", BODY),
        Paragraph("Student Information", H2),
        kv_table([
            ["Student legal name", p["name"]],
            ["Preferred name", p["preferred"]],
            ["Date of birth", p["dob"]],
            ["Gender", p["gender"]],
            ["Admission type", "First-year student"],
            ["Home address", p["address"]],
            ["Student email", p["email"]],
            ["Phone", p["phone"]],
            ["Previous school", p["prev_school"]],
            ["High school graduation", p["hs_grad"]],
        ]),
        Paragraph("Academic Program", H2),
        kv_table([
            ["Start term", "Fall 2026 (starts August 31, 2026)"],
            ["Enrollment status", p["status"]],
            ["Intended major", p["major"]],
            ["Delivery", "100% online"],
            ["Requested courses", p["courses"]],
            ["Transfer / AP credit", p["ap"]],
            ["Financial aid applied", p["aid"]],
        ]),
        PageBreak(),
        Paragraph("Emergency Contacts", H2),
        kv_table(contact_rows),
        Paragraph("Health and Accessibility", H2),
        kv_table([
            ["Immunization record submitted", "Yes"],
            ["Known allergies", p["allergies"]],
            ["Physician", p["physician"]],
            ["Requesting disability accommodations", p["accommodations"]],
            ["Honors program interest", p["honors"]],
        ]),
        Paragraph("Consents", H2),
        kv_table([
            ["Share records with parents (FERPA waiver)", p["ferpa"]],
            ["Directory information release", p["directory"]],
            ["Photo / media release", p["photo"]],
            ["Technology acceptable-use policy", "Agreed"],
        ]),
        Paragraph("Signature", H2),
        Paragraph("I certify that the information provided is accurate and complete.", BODY),
        Spacer(1, 18),
        kv_table([
            ["Student signature", p["name"]],
            ["Date signed", p["submitted"]],
        ]),
        Spacer(1, 18),
        Paragraph("<i>Sample document with fictitious data, for software testing only.</i>", BODY),
    ]
    doc.build(s)


# ---------- Student handbook ----------
SECTIONS = [
    ("1. Welcome", [
        f"Welcome to {SCHOOL}, a fully online, regionally accredited university offering associate, "
        "bachelor's and master's degrees. Our mission is to give working and traditional students a "
        "flexible, supportive path to a degree from wherever they live.",
        "Academic terms are 15 weeks in fall and spring and 8 weeks in summer. The Student Services office is "
        "open Monday to Friday, 8:00 AM to 6:00 PM Central Time. Reach it at (555) 010-4200 or "
        "services@mapleridge-university.example.",
    ]),
    ("2. Attendance and Participation", [
        "Online courses have no set meeting times unless the syllabus says otherwise, but students must "
        "participate each week. Participation means submitting at least one graded activity or discussion "
        "post per course per week.",
        "A student who does not participate for 14 consecutive days is reported to their advisor. A student "
        "who never participates during the first week may be administratively dropped from the course and "
        "will receive a full tuition refund.",
    ]),
    ("3. Grading and Late Work", [
        "Letter grades carry these points: A 4.0, B 3.0, C 2.0, D 1.0 and F 0.0, with plus and minus grades "
        "adjusting by 0.3. Undergraduates must keep a cumulative GPA of at least 2.0 to remain in good "
        "academic standing.",
        "Late work policies are set by each instructor and listed in the syllabus. Unless the syllabus says "
        "otherwise, late work loses 10 percent per day for up to 5 days and is not accepted after that. "
        "Students may request an extension before the deadline for documented illness, military service or "
        "family emergency.",
        "A student whose term GPA falls below 2.0 is placed on academic probation. Two consecutive terms on "
        "probation may lead to academic suspension.",
    ]),
    ("4. Degree Requirements", [
        "A bachelor's degree requires 120 credit hours: 36 hours of general education, 48 to 60 hours in "
        "the major and the remainder in electives. At least 30 of the last 60 hours must be completed at "
        f"{SCHOOL}.",
        "Up to 60 credit hours may be transferred from regionally accredited institutions. Advanced "
        "Placement (AP) exam scores of 3 or higher may earn credit in the corresponding course.",
    ]),
    ("5. Tuition, Refunds and Financial Aid", [
        "Tuition is $325 per credit hour for undergraduates. A technology fee of $75 is charged each term.",
        "Students who drop a course by the end of the first week receive a 100 percent refund. Dropping in "
        "weeks two and three earns a 50 percent refund. After week three there is no refund.",
        "Students receiving federal aid must maintain Satisfactory Academic Progress: a cumulative GPA of at "
        "least 2.0 and completion of at least 67 percent of attempted credit hours.",
    ]),
    ("6. Technology Requirements", [
        "Students need a computer made in the last five years, a webcam, a microphone and reliable "
        "broadband internet. Technical support is available 24 hours a day at help@mapleridge-university.example.",
        "Students on federal aid who lack a suitable computer may apply for a loaner laptop through the "
        "Student Services office. Loaner devices must be returned within 14 days of withdrawal.",
    ]),
    ("7. Academic Integrity", [
        "Plagiarism, cheating and unauthorized use of generative AI tools on graded work violate the academic "
        "integrity policy. A first offense results in a zero on the assignment and a report to the Dean of "
        "Students. A second offense may result in failure of the course. A third may lead to dismissal.",
        "Proctored exams use remote proctoring software. Students are asked to show their workspace on camera.",
    ]),
    ("8. Health and Wellness", [
        "All students have access to free telehealth counseling, with up to 8 sessions per year. Call "
        "(555) 010-4250 to schedule. Students who have allergies or medical conditions and plan to attend "
        "an on-campus residency week should tell Student Services at least 14 days before it begins.",
        "In a crisis, students should call 988 or local emergency services.",
    ]),
    ("9. Disability Services", [
        "Students with documented disabilities may request reasonable accommodations through the Office of "
        "Accessibility. Requests should be submitted at least 3 weeks before the start of a term, along with "
        "documentation from a qualified professional. Accommodations are not retroactive.",
    ]),
    ("10. Withdrawal and Leave of Absence", [
        "To withdraw from the university, a student submits the withdrawal form to the Registrar. Courses "
        "dropped after week three but before week ten appear on the transcript with a W. After week ten, "
        "the student receives the grade earned.",
        "A student may take up to two consecutive terms of leave of absence without reapplying. Students "
        "with federal loans should speak with financial aid first, because repayment may begin.",
    ]),
    ("11. Privacy of Student Records", [
        "The university follows the Family Educational Rights and Privacy Act (FERPA). At the university "
        "level, rights over education records belong to the student, not to the student's parents. The "
        "university shares records with a parent or other person only when the student has signed a consent "
        "form. Directory information is shared only if the student has opted in. Student records are never "
        "sold.",
    ]),
]


def handbook():
    doc = SimpleDocTemplate(str(out / "student_handbook.pdf"), pagesize=letter,
                            leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch)
    s = [Paragraph(SCHOOL, H1), Paragraph("Student Handbook, 2026-2027", ss["Heading2"]),
         Spacer(1, 12)]
    for title, paras in SECTIONS:
        s.append(Paragraph(title, H2))
        s.extend(Paragraph(p, BODY) for p in paras)
        s.append(Spacer(1, 6))
    s.append(Spacer(1, 12))
    s.append(Paragraph("<i>Fictitious university and sample policies, for software testing only.</i>", BODY))
    doc.build(s)


# ---------- High school transcript: Sarah Wilson ----------
TRANSCRIPT_YEARS = [
    ("Grade 9 (2022-2023)", [
        ["English 9", "A", "1.0"], ["Algebra II", "A", "1.0"], ["Biology", "A-", "1.0"],
        ["World History", "B+", "1.0"], ["Spanish I", "A", "1.0"], ["Physical Education", "A", "0.5"],
    ]),
    ("Grade 10 (2023-2024)", [
        ["English 10", "A-", "1.0"], ["Geometry", "A", "1.0"], ["Chemistry", "B+", "1.0"],
        ["U.S. History", "A", "1.0"], ["Spanish II", "A-", "1.0"], ["Intro to Computer Science", "A", "0.5"],
    ]),
    ("Grade 11 (2024-2025)", [
        ["AP English Language", "A-", "1.0"], ["Pre-Calculus", "A", "1.0"], ["Physics", "B+", "1.0"],
        ["Government", "A", "0.5"], ["AP Computer Science Principles", "A", "1.0"], ["Health", "A", "0.5"],
    ]),
    ("Grade 12 (2025-2026)", [
        ["English 12", "A", "1.0"], ["AP Calculus AB", "A", "1.0"], ["Economics", "A-", "0.5"],
        ["Statistics", "A", "1.0"], ["Art", "A", "0.5"], ["Computer Programming", "A", "1.0"],
    ]),
]


def transcript():
    doc = SimpleDocTemplate(str(out / "transcript_sarah_wilson.pdf"), pagesize=letter,
                            leftMargin=inch, rightMargin=inch, topMargin=0.8 * inch, bottomMargin=0.8 * inch)
    s = [
        Paragraph("Springfield Central High School", H1),
        Paragraph("Official Academic Transcript", ss["Heading3"]),
        Paragraph("1200 Capitol Avenue, Springfield, IL 62701 &nbsp;|&nbsp; Registrar: (217) 555-0120", BODY),
        Paragraph("Student", H2),
        kv_table([
            ["Student name", "Sarah Elizabeth Wilson"],
            ["Date of birth", "March 9, 2008"],
            ["Student ID", "SCHS-2022-3381"],
            ["Entered", "August 2022"],
            ["Graduated", "May 2026"],
            ["Diploma", "Standard diploma with honors"],
        ]),
    ]
    for title, courses in TRANSCRIPT_YEARS:
        s.append(Paragraph(title, H2))
        t = Table([["Course", "Grade", "Credit"]] + courses, colWidths=[3.8 * inch, 1.2 * inch, 1.2 * inch])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
        ]))
        s.append(t)
    s.append(Paragraph("Summary", H2))
    s.append(kv_table([
        ["Total credits earned", "26.0"],
        ["Cumulative GPA (unweighted, 4.0 scale)", "3.82"],
        ["Cumulative GPA (weighted)", "4.01"],
        ["Class rank", "14 of 212"],
        ["AP exams", "AP English Language (4), AP Calculus AB (4)"],
    ]))
    s.append(Spacer(1, 18))
    s.append(Paragraph("Certified by: Karen Ellis, Registrar &nbsp;&nbsp; Date issued: June 12, 2026", BODY))
    s.append(Spacer(1, 12))
    s.append(Paragraph("<i>Sample document with fictitious data, for software testing only.</i>", BODY))
    doc.build(s)


for student in STUDENTS:
    enrollment(student)
handbook()
transcript()
print("done")
