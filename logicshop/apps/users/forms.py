from django import forms


# 注册
class RegisterForm(forms.Form):
    username = forms.CharField(max_length=20, min_length=5, required=True, error_messages={
        'max_length': '用户名最长为20',
        'min_length': '用户名最短为5'
    })
    password = forms.CharField(max_length=20, min_length=8, required=True)
    password2 = forms.CharField(max_length=20, min_length=8, required=True)
    mobile = forms.CharField(max_length=11, min_length=11, required=True)
    sms_code = forms.CharField(max_length=6, min_length=6, required=True)

    def clean(self):
        # clean_data 即为前端返回给后端的所有数据 调用父类的方法 但也使父类的方法生效
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if password2 != password:
            raise forms.ValidationError('两次密码不一致！！')
        return cleaned_data


# 登录
class LoginForm(forms.Form):
    username = forms.CharField(max_length=20, min_length=5)
    password = forms.CharField(max_length=20, min_length=8)
    remembered = forms.BooleanField(required=False)
