from django import forms

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label='Registered Email', max_length=254)

class OTPVerificationForm(forms.Form):
    otp_code = forms.CharField(label='Enter OTP', max_length=6)

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(label='New Password', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
