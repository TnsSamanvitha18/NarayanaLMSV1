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

def award_badge(learner_id, badge_name, icon, description):
    """
    Awards a badge to a learner if they don't have it yet, and generates a notification.
    """
    from app.models.badge import LearnerBadge
    
    # Check if they already have this badge
    existing = LearnerBadge.query.filter_by(learner_id=learner_id, badge_name=badge_name).first()
    if existing:
        return False
        
    badge = LearnerBadge(
        learner_id=learner_id,
        badge_name=badge_name,
        icon=icon,
        description=description
    )
    db.session.add(badge)
    
    # Generate notification so they know they earned a badge
    notification = LearnerNotification(
        learner_id=learner_id,
        title="New Badge Unlocked! 🏆",
        message=f"Congratulations! You unlocked the '{badge_name}' badge: {description}.",
        notification_type='BADGE_EARNED'
    )
    db.session.add(notification)
    
    # Let's also award them some bonus points (e.g. 50 points) for earning a badge
    learner = Learner.query.get(learner_id)
    if learner:
        if learner.points is None:
            learner.points = 0
        learner.points += 50
        
    db.session.commit()
    return True

