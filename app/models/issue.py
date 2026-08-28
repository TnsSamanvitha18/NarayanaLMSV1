from datetime import datetime
from app.models import db

class LmsIssue(db.Model):
    __tablename__ = 'lms_issues'

    id = db.Column(db.Integer, primary_key=True)
    learner_id = db.Column(db.Integer, db.ForeignKey('learners.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Technical') # 'Technical', 'Content', 'Certificate', 'Other'
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Open') # 'Open', 'Resolved'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    learner = db.relationship('Learner', backref=db.backref('issues', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<LmsIssue {self.id} - {self.category} ({self.status})>'
