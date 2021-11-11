let vm = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'], //修改vue读取变量的方法  mustache语法
    data: {
        // v-model
        username: '',
        password: '',
        password2: '',
        mobile: '',
        allow: '',
        image_code: '',
        sms_code: '',
        sms_code_tip: '获取短信验证码',
        send_flag: false, //前端短信发送过于频繁
        // v-show
        error_name: false,
        error_password: false,
        error_password2: false,
        error_mobile: false,
        error_allow: false,
        error_code: false,
        error_sms_code: false,
        uuid: '',
        // v-bind
        image_code_url: '',

        //error_message
        error_name_message: '',
        error_mobile_message: '',
        error_password_message: '',
        error_code_message: '',
        error_sms_code_message: '',
    },
    // 页面加载完成后被调用的方法
    mounted() {
        // 生成图形验证码
        this.generate_image_code();
    },
    methods: {
        // 点击发送短信验证码 'sms_codes/(?P<mobile>1[3-9]\d{9})/$'
        send_sms_code() {
            if (this.send_flag === true) {
                // 上锁了
                return;
            }
            this.send_flag = true;

            let url = '/sms_codes/' + this.mobile + '/?uuid=' + this.uuid + '&image_code=' + this.image_code;
            axios.get(url, {
                responseType: 'json'
            })
                .then(response => {
                    if (response.data.code === '0') {
                        // 发送短信成功 展示倒计时60秒
                        let num = 60
                        // setInterval('回调函数','时间间隔（毫秒）')
                        let t = setInterval(() => {
                            if (num === 1) {
                                // 停止回调函数
                                clearInterval(t);
                                this.sms_code_tip = '获取短信验证码'
                                // 重新生成图片验证码
                                this.generate_image_code();
                                this.send_flag = false
                            } else {
                                num -= 1;
                                this.sms_code_tip = num + '秒'

                            }
                        }, 1000)
                    } else {
                        if (response.data.code === '4001') {
                            // 图形验证码错误
                            this.error_sms_code_message = response.data.errmsg;
                            this.error_sms_code = true
                        } else {
                            // 短信验证码错误
                            this.error_sms_code_message = response.data.errmsg;
                            this.error_sms_code = true
                        }
                        this.send_flag = false
                    }
                })
                .catch(error => {
                    console.log(error.response);
                    this.send_flag = false
                })

        },
        // 生成图片验证码
        generate_image_code() {
            // uuid的生成
            this.uuid = generateUUID();
            this.image_code_url = '/image_codes/' + this.uuid + '/'
        },
        // 检查用户名
        check_username() {
            // 正则匹配不能加空格{5,20}
            let re = /^[a-zA-Z0-9_-]{5,20}$/;
            if (re.test(this.username)) {
                // 匹配成功，则不展示
                this.error_name = false;
            } else {
                // 匹配失败，则进行展示
                this.error_name = true;
                this.error_name_message = '请输入5-20个字符的用户名'
            }
            if (this.error_name === false) {
                // ajax向后端发送请求
                let url = '/usernames/' + this.username + '/count/';
                // axios.get(url,请求头(字典))
                axios.get(url, {
                    responseType: 'json'
                })
                    // response 后端向前端返回json数据
                    .then(response => {
                        // 取出返回的json数据中的count 进行判断
                        if (response.data.count === 1) {
                            // count 为1 将错误信息展示到前端
                            this.error_name_message = '用户名已存在';
                            this.error_name = true;
                        } else {
                            this.error_name = false;
                        }

                    })
                    // 请求不成功
                    .catch(error => {
                        console.log(error.response)
                    })
            }
        },
        check_password() {
            let re = /^[a-zA-Z0-9]{8,20}$/;
            this.error_password = !re.test(this.password);
        },
        check_password2() {
            this.error_password2 = this.password !== this.password2;
        },
        check_mobile() {
            let re = /^1[3-9]\d{9}$/;
            if (re.test(this.mobile)) {
                this.error_mobile = false;
            } else {
                this.error_mobile = true;
                this.error_mobile_message = '请输入正确的手机号'
            }
            if (this.error_mobile === false) {
                //ajax向后端发送请求 请求数据 get 以此路由向后端请求数据
                let url = '/mobile/' + this.mobile + '/count/';
                // 请求参数 url 请求头
                axios.get(url, {
                    responseType: 'json'
                })
                    // response 将响应数据返回给前端
                    .then(response => {
                        if (response.data.count === 1) {
                            this.error_mobile_message = '手机号码已存在';
                            this.error_mobile = true

                        } else {
                            this.error_mobile = false
                        }
                    })
                    .catch(error => {
                        console.log(error.response)
                    })

            }
        },
        check_allow() {
            // 单选框传递过来的 allow 选中就是true
            this.error_allow = !this.allow;
        },
        // 检查图形验证码
        check_image_code() {
            if (this.image_code.length !== 4) {
                this.error_code = true;
                this.error_code_message = '图形验证码长度为4'
            } else {
                this.error_code = false
            }
        },
        // 检查短信验证码
        check_sms_code() {
            if (this.sms_code.length !== 6) {
                this.error_sms_code_message = '请输入短信验证码';
                this.error_sms_code = true;
            } else {
                this.error_sms_code = false;
            }
        },
        on_submit() {
            //禁用到表单的提交事件 全部方法通过才让提交数据给后端
            if (this.error_name || this.error_password || this.error_password2 || this.error_mobile || this.error_allow) {
                // 禁止表单提交
                return window.event.returnValue = false;
            }
        }
    }
})