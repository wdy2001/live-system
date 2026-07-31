import React from 'react'
import {
  Form,
  Select,
  Radio,
  Input,
  Button,
  Upload,
  message,
  Result,
  Space,
} from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { createRepair } from '@/api/repair'
import { repairTypeOptions } from '@/utils/mapping'

const { Option } = Select
const { TextArea } = Input
const { Dragger } = Upload

function RepairCreate() {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = React.useState(false)
  const [result, setResult] = React.useState(null)

  const onFinish = async (values) => {
    setLoading(true)
    try {
      const payload = { ...values }
      if (values.images && values.images.fileList) {
        payload.images = values.images.fileList
          .filter((f) => f.status === 'done' || f.originFileObj)
          .map((f) => f.name || (f.originFileObj && f.originFileObj.name))
          .filter(Boolean)
      }
      delete payload.images
      const data = await createRepair(payload)
      setResult(data || { success: true })
      message.success('报修提交成功')
    } catch (e) {
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return (
      <Result
        status="success"
        title="报修提交成功"
        subTitle={`工单号：${result.id || result.order_no || '已受理'}`}
        extra={[
          <Space key="btns">
            <Button onClick={() => {
              setResult(null)
              form.resetFields()
            }}>
              继续提交
            </Button>
            <Button type="primary" onClick={() => navigate('/repair/list')}>
              查看报修进度
            </Button>
          </Space>,
        ]}
      />
    )
  }

  const dummyUploadProps = {
    name: 'file',
    multiple: true,
    beforeUpload: () => false,
    fileList: [],
  }

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        requiredMark
        initialValues={{ urgency: 'middle' }}
      >
        <Form.Item
          label="报修类型"
          name="repair_type"
          rules={[{ required: true, message: '请选择报修类型' }]}
        >
          <Select placeholder="请选择报修类型" size="large">
            {repairTypeOptions.map((o) => (
              <Option key={o.value} value={o.value}>
                {o.label}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          label="紧急程度"
          name="urgency"
          rules={[{ required: true, message: '请选择紧急程度' }]}
        >
          <Radio.Group size="large">
            <Radio.Button value="low">一般</Radio.Button>
            <Radio.Button value="middle">紧急</Radio.Button>
            <Radio.Button value="high">非常紧急</Radio.Button>
          </Radio.Group>
        </Form.Item>

        <Form.Item
          label="报修地址"
          name="address"
          rules={[{ required: true, message: '请输入报修地址' }]}
        >
          <Input placeholder="请输入详细地址（小区/楼栋/房号）" size="large" />
        </Form.Item>

        <Form.Item
          label="联系人"
          name="contact"
          rules={[{ required: true, message: '请输入联系人姓名' }]}
        >
          <Input placeholder="请输入联系人姓名" size="large" />
        </Form.Item>

        <Form.Item
          label="联系电话"
          name="phone"
          rules={[
            { required: true, message: '请输入联系电话' },
            { pattern: /^1\d{10}$/, message: '请输入正确的11位手机号' },
          ]}
        >
          <Input placeholder="11位手机号" size="large" />
        </Form.Item>

        <Form.Item
          label="问题描述"
          name="description"
          rules={[{ required: true, message: '请描述故障情况' }]}
        >
          <TextArea
            rows={5}
            placeholder="请详细描述故障发生的情况（时间、现象等）"
            showCount
            maxLength={500}
          />
        </Form.Item>

        <Form.Item label="现场图片（可选）" name="images">
          <Dragger {...dummyUploadProps} height={140}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽图片到此区域上传</p>
            <p className="ant-upload-hint" style={{ fontSize: 12 }}>
              支持多图上传，仅作占位演示，不实际上传文件
            </p>
          </Dragger>
        </Form.Item>

        <Form.Item style={{ marginTop: 24 }}>
          <Space>
            <Button type="primary" htmlType="submit" size="large" loading={loading}>
              提交报修
            </Button>
            <Button size="large" onClick={() => navigate('/repair/list')}>
              查看报修列表
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  )
}

export default RepairCreate
