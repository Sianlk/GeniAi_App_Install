# Educational Content Generation
import pdf_generator
import course_builder

def create_educational_content(template):
    print("Creating educational content...")
    pdf = pdf_generator.generate(template)
    course = course_builder.build_course(template)
    return pdf, course
