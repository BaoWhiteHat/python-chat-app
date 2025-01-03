from flask import render_template, request, flash, redirect, url_for, session as flask_session
from flask_login import login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cyber_app.models.models import User, db, Session
from datetime import datetime, timedelta


class AuthController:
    def __init__(self):
        pass

    def login(self):
        """Handle user login and create a session in the database."""
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')

            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                have_session = self.validate_session()
                if have_session is None:
                    # Create a new session
                    session_id = self.create_session(user)

                    # Store session ID in a secure cookie
                    flask_session['session_id'] = session_id

                flash('Logged in successfully!', category='success')
                return redirect(url_for('chat.chat'))

            flash('Invalid email or password.', category='error')

        return render_template("login.html", user=current_user)

    def create_session(self, user):
        """Create a session record in the database after invalidating existing ones."""
        # Invalidate existing sessions for the user
        existing_sessions = Session.query.filter_by(user_id=user.id).all()
        for session in existing_sessions:
            db.session.delete(session)

        # Create a new session
        expires_at = datetime.utcnow() + timedelta(days=7)  # Session valid for 7 days
        new_session = Session(user_id=user.id, expires_at=expires_at)
        db.session.add(new_session)
        db.session.commit()
        return new_session.id

    @login_required
    def logout(self):
        """Handle user logout and delete the session."""
        session_id = flask_session.pop('session_id', None)
        if session_id:
            self.delete_session(session_id)
        logout_user()
        flash('Logged out successfully.', category='success')
        return redirect(url_for('auth.login'))

    def delete_session(self, session_id):
        """Delete a session record from the database."""
        session = Session.query.get(session_id)
        if session:
            db.session.delete(session)
            db.session.commit()

    def sign_up(self):
        """Handle user registration."""
        if request.method == 'POST':
            email = request.form.get('email')
            username = request.form.get('username')
            password1 = request.form.get('password1')
            password2 = request.form.get('password2')

            if User.query.filter_by(email=email).first():
                flash('Email already exists.', category='error')
            elif len(email) < 4:
                flash('Email must be greater than 3 characters.', category='error')
            elif password1 != password2:
                flash('Passwords do not match.', category='error')
            elif len(password1) < 7:
                flash('Password must be at least 7 characters.', category='error')
            elif len(username) < 3:
                flash('Username must be at least 3 characters.', category='error')
            else:
                hashed_password = generate_password_hash(password1, method='pbkdf2:sha256')
                new_user = User(email=email, username=username, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()

                # Log in the user and create a session
                session_id = self.create_session(new_user)
                flask_session['session_id'] = session_id

                flash('Account created successfully!', category='success')
                return redirect(url_for('chat.chat'))

        return render_template("sign_up.html", user=current_user)

    def validate_session(self):
        """Validate the session ID stored in the cookie."""
        session_id = flask_session.get('session_id')
        if not session_id:
            return None

        session = Session.query.get(session_id)
        if not session or session.expires_at < datetime.utcnow():
            # Session is invalid or expired
            flask_session.pop('session_id', None)
            if session:
                db.session.delete(session)
                db.session.commit()
            return None

        return session.user_id
