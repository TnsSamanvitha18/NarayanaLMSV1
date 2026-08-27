import re
from markupsafe import escape, Markup
from app.models import db
from app.models.user import Learner
from app.models.notification import LearnerNotification

def process_tags_and_notify(content, author_name, post_or_comment_text):
    """
    Scans content for '@10001' tags and generates LearnerNotifications for each mentioned learner.
    """
    if not content:
        return
        
    # Match Global IDs of length 5 or more (e.g. @10001, @10002)
    tags = re.findall(r'@(\d{5,})', content)
    notified_ids = set()
    
    for gid in tags:
        if gid in notified_ids:
            continue
            
        learner = Learner.query.filter_by(global_id=gid).first()
        if learner:
            # Create a notification preview
            preview = post_or_comment_text[:60] + "..." if len(post_or_comment_text) > 60 else post_or_comment_text
            notif = LearnerNotification(
                learner_id=learner.id,
                title="You were tagged on the Learning Wall",
                message=f"{author_name} tagged you: \"{preview}\"",
                notification_type='TAGGED'
            )
            db.session.add(notif)
            notified_ids.add(gid)
            
    if notified_ids:
        db.session.commit()

def format_tags_filter(text):
    """
    Jinja filter: Escapes text for XSS safety, then replaces '@10001' tags with HTML name badges.
    """
    if not text:
        return ""
        
    escaped_text = str(escape(text))
    
    def replace_tag(match):
        gid = match.group(1)
        learner = Learner.query.filter_by(global_id=gid).first()
        if learner:
            # Return a styled pill containing their actual name
            return f'<span class="badge bg-teal-subtle text-teal border border-teal-subtle px-1.5 py-0.5 rounded-pill fw-bold">@{learner.name}</span>'
        return match.group(0) # Fallback to raw @10001 if learner doesn't exist
        
    processed = re.sub(r'@(\d{5,})', replace_tag, escaped_text)
    return Markup(processed)
