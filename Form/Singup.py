from wtforms import Form, StringField, PasswordField, validators,BooleanField,SubmitField

class SingupForm(Form):
    username = StringField('نام کاربری', [
        validators.Length(min=4, max=25),
        validators.DataRequired(message="این فیلد اجباری است")
    ])
    password = PasswordField('رمز عبور', [
        validators.DataRequired(),
    ])
    password2 =  PasswordField('تکرار رمز عبور', [
        validators.DataRequired(),
    ])