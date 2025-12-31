from wtforms import Form, StringField, PasswordField, validators,BooleanField,SubmitField

class LoginForm(Form):
    username = StringField('نام کاربری', [
        validators.Length(min=4, max=25),
        validators.DataRequired(message="این فیلد اجباری است")
    ])
    password = PasswordField('رمز عبور', [
        validators.DataRequired(),
    ])
    remember = BooleanField(
        "مرا به خاطر بسپار"
    )