# Feed360 Feedback Module

## Quick Developer Notes

- **Environment Variables:**
  - `PERPLEXITY_API_KEY` (for future AI analysis)
- **Migration Commands:**
  - `python manage.py makemigrations feed360`
  - `python manage.py migrate`
- **Enable async analysis:**
  - To use Celery for async sentiment analysis, add Celery config and update `analyze_text_with_perplexity` to use a task.
- **Testing:**
  - Run `python manage.py test feed360`
- **Models:**
  - FeedbackForm, FeedbackQuestion, FeedbackResponse, FeedbackAggregate
- **Permissions:**
  - Only HODs can create/view all results; staff see only their own; students submit feedback.
- **Templates:**
  - All templates in `templates/feed360/`
