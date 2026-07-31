import React from 'react'
import { Form, Input, Button, Card, message } from 'antd'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '@/api/auth'

function Register() {
  const navigate = useNavigate()
  const [loading, setLoading] = React.useState(false)
  const [form] = Form.useForm()

  const onFinish = async (values) => {
    setLoading(true)
    try {
      await register(values)
      message.success('注册成功，请登录')
      navigate('/login', { replace: true })
    } catch (e) {
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #f0f5ff 0%, #d6e4ff 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
      }}
    >
      <Card
        title={<h2 style={{ margin: 0, textAlign: 'center' }}>生活缴费系统 - 注册</h2>}
        style={{ width: 480, boxShadow: '0 8px 24px rgba(0,0,0,0.08)' }}
      >
        <Form
          form={form}
          name="register"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
          layout="vertical"
        >
          <Form.Item
            label="用户名"
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>

          <Form.Item
            label="密码"
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6位' },
            ]}
          >
            <Input.Password placeholder="请输入密码（至少6位）" />
          </Form.Item>

          <Form.Item
            label="确认密码"
            name="confirm_password"
            dependencies={['password']}
            rules={[
              { required: true, message: '请再次输入密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password placeholder="请再次输入密码" />
          </Form.Item>

          <Form.Item
            label="手机号"
            name="phone"
            rules={[
              { required: true, message: '请输入手机号' },
              { pattern: /^1\d{10}$/, message: '请输入正确的11位手机号' },
            ]}
          >
            <Input placeholder="11位手机号" />
          </Form.Item>

          <Form.Item label="姓名" name="name">
            <Input placeholder="姓名（选填）" />
          </Form.Item>

          <Form.Item label="地址" name="address">
            <Input placeholder="地址（选填）" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              注册
            </Button>
          </Form.Item>
        </Form>
        <div style={{ textAlign: 'center' }}>
          已有账号？<Link to="/login">去登录</Link>
        </div>
      </Card>
    </div>
  )
}

export default Register
