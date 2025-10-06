from Application import create_app
from Application.models import db

app = create_app('ProductionConfig')

# Create table
with app.app_context():
    db.create_all()

app.run()