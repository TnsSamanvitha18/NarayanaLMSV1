from datetime import datetime
from app.models import db

class LearnerEnrollment(db.Model):
    __tablename__ = 'learner_enrollments'

    id = db.Column(db.Integer, primary_key=True)
    learner_id = db.Column(db.Integer, db.ForeignKey('learners.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('live_classes.id'), nullable=True)

    completion_status = db.Column(db.String(30), nullable=False, default='Enrolled') # 'Enrolled', 'In Progress', 'Completed', 'Failed'
    current_lesson = db.Column(db.Integer, default=1)
    attempts_count = db.Column(db.Integer, default=0) # For Self Paced assessments (max 3)
    final_score = db.Column(db.Float, nullable=True)

    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime, nullable=True)
    extended_deadline = db.Column(db.DateTime, nullable=True)
    extension_requested = db.Column(db.Boolean, default=False, nullable=True)

    assessment_attempts = db.relationship('AssessmentAttempt', backref='enrollment', lazy=True, cascade='all, delete-orphan')

    @property
    def is_expired(self):
        from datetime import datetime
        from app.models.live_class import LiveClass
        
        # Check course target completion date
        if self.course.completion_date and self.course.completion_date < datetime.utcnow():
            if self.extended_deadline and self.extended_deadline >= datetime.utcnow():
                return False
            return True
            
        # Check live class date if applicable
        if self.class_id:
            live_cl = LiveClass.query.get(self.class_id)
            if live_cl and ((live_cl.class_date < datetime.utcnow().date()) or live_cl.is_locked):
                if self.extended_deadline and self.extended_deadline.date() >= datetime.utcnow().date():
                    return False
                return True
                
        return False

    def __repr__(self):
        return f'<Enrollment Learner {self.learner_id} - Course {self.course_id}>'


class AssessmentAttempt(db.Model):
    __tablename__ = 'assessment_attempts'

    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('learner_enrollments.id'), nullable=False)
    assessment_type = db.Column(db.String(20), nullable=False) # 'PRE', 'POST', 'LESSON'
    lesson_number = db.Column(db.Integer, nullable=True, default=1)
    lesson_id = db.Column(db.Integer, db.ForeignKey('course_lessons.id'), nullable=True)
    score_percentage = db.Column(db.Float, nullable=False)
    passed = db.Column(db.Boolean, nullable=False, default=False)
    attempt_number = db.Column(db.Integer, nullable=False, default=1)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AssessmentAttempt {self.assessment_type} - {self.score_percentage}%>'


class LessonReview(db.Model):
    __tablename__ = 'lesson_reviews'

    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('learner_enrollments.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('course_lessons.id'), nullable=False)
    reviewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LessonReview Enrollment {self.enrollment_id} - Lesson {self.lesson_id}>'
