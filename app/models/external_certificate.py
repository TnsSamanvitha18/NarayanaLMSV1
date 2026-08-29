from datetime import datetime
from app.models import db

class ExternalCertificate(db.Model):
    __tablename__ = 'external_certificates'

    id = db.Column(db.Integer, primary_key=True)
    learner_id = db.Column(db.Integer, db.ForeignKey('learners.id'), nullable=False)
    course_name = db.Column(db.String(255), nullable=False)
    issuing_org = db.Column(db.String(255), nullable=False)
    date_earned = db.Column(db.Date, nullable=False)
    pdf_filename = db.Column(db.String(255), nullable=True)
    skills = db.Column(db.Text, nullable=True) # Comma-separated tags, e.g. "Python, SQL, Analytics"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    learner = db.relationship('Learner', backref=db.backref('external_certificates', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<ExternalCertificate {self.course_name} for Learner {self.learner_id}>'
