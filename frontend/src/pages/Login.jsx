import React from 'react'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '@/api/auth'
import { setToken, setUser } from '@/utils/auth'

function Login() {
  const navigate = useNavigate()
  const [loading, setLoading] = React.useState(false)

  const onFinish = async (values) => {
    setLoading(true)
    try {
      const res = await login(values)
      const token = res?.access_token || res?.token || ''
      const user = res?.user || { username: values.username }
      if (token) {
        setToken(token)
      }
      setUser(user)
      message.success('登录成功')
      navigate('/', { replace: true })
    } catch (e) {
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #e6f4ff 0%, #bae0ff 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
      }}
    >
      <Card
        title={<h2 style={{ margin: 0, textAlign: 'center' }}>生活缴费系统 - 登录</h2>}
        style={{ width: 420, boxShadow: '0 8px 24px rgba(0,0,0,0.08)' }}
      >
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
          initialValues={{ username: '', password: '' }}
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6位' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              登录
            </Button>
          </Form.Item>
        </Form>
        <div style={{ textAlign: 'center' }}>
          还没账号？<Link to="/register">去注册</Link>
        </div>
      </Card>
    </div>
  )
}

export default Login
