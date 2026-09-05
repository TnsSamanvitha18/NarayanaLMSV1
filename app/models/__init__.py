from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models to ensure registration for db.create_all() and migrations
from app.models.user import AdminUser, Learner
from app.models.course import Course, CourseLesson, CourseAssessment, LessonCourseware, CoursewareAudioTrack, CourseMaterial, RiseCoursewareVersion, LearnerBlockProgress
from app.models.live_class import LiveClass, AuditLog
from app.models.enrollment import LearnerEnrollment, AssessmentAttempt, LessonReview
from app.models.badge import LearnerBadge
from app.models.feedback import FeedbackRepository, FeedbackQuestion, FeedbackResponse
from app.models.learning_wall import LearningWallPost, LearningWallReaction
from app.models.notification import LearnerNotification
from app.models.issue import LmsIssue
from app.models.external_certificate import ExternalCertificate

