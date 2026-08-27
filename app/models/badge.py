from datetime import datetime
from app.models import db

class LearnerBadge(db.Model):
    __tablename__ = 'learner_badges'

    id = db.Column(db.Integer, primary_key=True)
    learner_id = db.Column(db.Integer, db.ForeignKey('learners.id'), nullable=False, index=True)
    badge_name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50), nullable=False, default='fa-award')
    description = db.Column(db.String(255), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LearnerBadge {self.badge_name} earned by Learner {self.learner_id}>'
