import React from 'react'
import {
  Card,
  Form,
  Input,
  Button,
  Avatar,
  Row,
  Col,
  Descriptions,
  message,
  Spin,
  Divider,
  Space,
} from 'antd'
import { UserOutlined, EditOutlined, SaveOutlined, RollbackOutlined } from '@ant-design/icons'
import { getMe, updateMe } from '@/api/user'
import { getUser, setUser } from '@/utils/auth'
import dayjs from 'dayjs'

function Profile() {
  const [form] = Form.useForm()
  const [info, setInfo] = React.useState(null)
  const [loading, setLoading] = React.useState(false)
  const [editing, setEditing] = React.useState(false)
  const [saving, setSaving] = React.useState(false)

  const fetchMe = React.useCallback(async () => {
    setLoading(true)
    try {
      const data = await getMe()
      if (data) {
        setInfo(data)
        setUser(data)
        form.setFieldsValue({
          name: data.name,
          phone: data.phone,
          address: data.address,
        })
      }
    } catch (e) {
      const localUser = getUser()
      if (localUser) {
        setInfo(localUser)
        form.setFieldsValue({
          name: localUser.name,
          phone: localUser.phone,
          address: localUser.address,
        })
      }
    } finally {
      setLoading(false)
    }
  }, [form])

  React.useEffect(() => {
    fetchMe()
  }, [fetchMe])

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      setSaving(true)
      try {
        const data = await updateMe(values)
        message.success('资料更新成功')
        const newInfo = { ...(info || {}), ...data, ...values }
        setInfo(newInfo)
        setUser(newInfo)
        setEditing(false)
      } catch (e) {
      } finally {
        setSaving(false)
      }
    } catch {}
  }

  const handleCancel = () => {
    form.setFieldsValue({
      name: info?.name,
      phone: info?.phone,
      address: info?.address,
    })
    setEditing(false)
  }

  return (
    <Spin spinning={loading}>
      {info && (
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Card style={{ textAlign: 'center' }}>
              <Avatar
                size={96}
                icon={<UserOutlined />}
                style={{
                  backgroundColor: '#1677ff',
                  marginBottom: 16,
                  fontSize: 40,
                }}
              />
              <h2 style={{ margin: 0, marginBottom: 4 }}>
                {info.name || info.username || '用户'}
              </h2>
              <p style={{ color: '#888', margin: 0 }}>
                @{info.username || 'user'}
              </p>
              <Divider />
              <Descriptions column={1} size="small">
                <Descriptions.Item label="用户ID">
                  {info.id || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="注册时间">
                  {info.created_at
                    ? dayjs(info.created_at).format('YYYY-MM-DD')
                    : '-'}
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </Col>
          <Col xs={24} md={16}>
            <Card
              title="个人资料"
              extra={
                !editing ? (
                  <Button
                    type="primary"
                    icon={<EditOutlined />}
                    onClick={() => setEditing(true)}
                  >
                    编辑
                  </Button>
                ) : (
                  <Space>
                    <Button
                      icon={<RollbackOutlined />}
                      onClick={handleCancel}
                      disabled={saving}
                    >
                      取消
                    </Button>
                    <Button
                      type="primary"
                      icon={<SaveOutlined />}
                      onClick={handleSave}
                      loading={saving}
                    >
                      保存
                    </Button>
                  </Space>
                )
              }
            >
              <Form
                form={form}
                layout="vertical"
                disabled={!editing}
                initialValues={{
                  name: info.name,
                  phone: info.phone,
                  address: info.address,
                }}
              >
                <Form.Item label="用户名">
                  <Input value={info.username} disabled />
                </Form.Item>
                <Form.Item
                  label="姓名"
                  name="name"
                  rules={editing ? [{ required: true, message: '请输入姓名' }] : []}
                >
                  <Input placeholder="请输入姓名" />
                </Form.Item>
                <Form.Item
                  label="手机号"
                  name="phone"
                  rules={
                    editing
                      ? [
                          { required: true, message: '请输入手机号' },
                          { pattern: /^1\d{10}$/, message: '请输入正确的11位手机号' },
                        ]
                      : []
                  }
                >
                  <Input placeholder="11位手机号" />
                </Form.Item>
                <Form.Item
                  label="地址"
                  name="address"
                  rules={editing ? [{ required: true, message: '请输入地址' }] : []}
                >
                  <Input.TextArea
                    rows={3}
                    placeholder="请输入详细地址"
                  />
                </Form.Item>
              </Form>
            </Card>
          </Col>
        </Row>
      )}
    </Spin>
  )
}

export default Profile
