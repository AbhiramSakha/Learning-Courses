from fpdf import FPDF

def generate_pdf(learners):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Learner Management Report", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=10)
    pdf.cell(40, 10, "ID", 1)
    pdf.cell(60, 10, "Name", 1)
    pdf.cell(90, 10, "Course", 1)
    pdf.ln()

    for learner in learners:
        pdf.cell(40, 10, learner[0], 1)
        pdf.cell(60, 10, learner[1], 1)
        pdf.cell(90, 10, learner[2], 1)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin1')  # return as bytes
