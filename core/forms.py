# Certificate Upload Form
from django import forms
from .models import CertificateUpload

class CertificateUploadForm(forms.ModelForm):
	class Meta:
		model = CertificateUpload
		fields = ['file', 'subject']
		widgets = {
			'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
		}
