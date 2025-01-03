from flask import render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cyber_app.models.models import User
from .base_controller import BaseController
from flask_cyber_app.models.models import db


class AuthController(BaseController):
    def __init__(self):
        super().__init__(model=User, template_folder=None)

    def login(self):
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')

            user = User.query.filter_by(email=email).first()
            if user:
                if check_password_hash(user.password, password):
                    flash('Logged in successfully!', category='success')
                    login_user(user, remember=True)
                    return redirect(url_for('views.home'))
                else:
                    flash('Incorrect password, try again.', category='error')
            else:
                flash('Email does not exist.', category='error')

        return self.render("login.html", context={"user": current_user})

    @login_required
    def logout(self):
        logout_user()
        return redirect(url_for('auth.login'))

    def sign_up(self):
        if request.method == 'POST':

            email = request.form.get('email')
            username = request.form.get('username')
            password1 = request.form.get('password1')
            password2 = request.form.get('password2')

            user = User.query.filter_by(email=email).first()
            if user:
                flash('Email already exists.', category='error')
            elif len(email) < 4:
                flash('Email must be greater than 3 characters.', category='error')
            elif password1 != password2:
                flash('Passwords don\'t match.', category='error')
            elif len(password1) < 7:
                flash('Password must be at least 7 characters.', category='error')
            elif len(username) < 3:
                flash('username must be at least 3 characters.', category='error')
            else:
                # Use the correct hashing method
                hashed_password = generate_password_hash(password1, method='pbkdf2:sha256')
                new_user = User(email=email, username=username, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user, remember=True)
                flash('Account created!', category='success')
                return render_template(url_for('chat.html', user= current_user))

        return render_template("sign_up.html", user=current_user)
