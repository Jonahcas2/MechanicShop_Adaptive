from Application import create_app
from Application.models import db

app = create_app('DevConfig')

# Create table
with app.app_context():
    db.create_all()

app.run()