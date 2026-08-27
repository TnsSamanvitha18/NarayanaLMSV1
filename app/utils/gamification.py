from app.models import db
from app.models.user import Learner
from app.models.notification import LearnerNotification

def award_points(learner_id, points, reason):
    """
    Awards points to a learner and generates a notification.
    """
    learner = Learner.query.get(learner_id)
    if not learner:
        return False
        
    if learner.points is None:
        learner.points = 0
        
    learner.points += points
    
    # Generate notification so the user knows they earned points
    notification = LearnerNotification(
        learner_id=learner.id,
        title="Points Earned! ⭐",
        message=f"You just earned {points} points for: {reason}. Keep up the great work!",
        notification_type='POINTS_EARNED'
    )
    
    db.session.add(notification)
    db.session.commit()
    return True
