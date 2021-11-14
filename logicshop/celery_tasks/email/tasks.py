# @Time: 2021/11/14-9:31
# @User: Ycx


from django.conf import settings
from django.core.mail import send_mail

# 创建任务 发送邮件
from celery_tasks.main import celery_app


# name 给任务取名字
@celery_app.task(name='send_verify_email')
def send_verify_email(email, verify_url):
    """
    发送邮件的异步任务
    :param email: 要发送的邮箱
    :param verify_url: 激活链接
    """

    subject = "商城邮箱验证"
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)
    send_mail(subject, '', from_email=settings.EMAIL_FROM, recipient_list=[email], html_message=html_message)
