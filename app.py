from flask import Flask
from flask_cors import CORS

from api import auth, listings, users
from extenstions import migrate, db, jwt
from models import Role, Permission
from utils import register_error_handlers


def seed_roles_and_permissions():
    if Role.query.filter_by(name='Admin').first():
        return

    admin_role = Role(name='Admin')
    user_role = Role(name='User')

    admin_permissions = [Permission(name='manage_users'), Permission(name='manage_content'), Permission(name='manage_roles')]
    user_permissions = [Permission(name='view_content')]

    admin_role.permissions.extend(admin_permissions)
    user_role.permissions.extend(user_permissions)

    db.session.add_all([admin_role, user_role])
    db.session.commit()
    print("Seeded roles and permissions")

def create_app():
    app = Flask(__name__)
    app.config.from_object("config")

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    register_error_handlers(app)

    app.register_blueprint(auth.auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(listings.listings_bp, url_prefix='/api/v1/listings')
    app.register_blueprint(users.users_bp, url_prefix='/api/v1/users')

    CORS(app)

    with app.app_context():
        db.create_all()
        seed_roles_and_permissions()
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

