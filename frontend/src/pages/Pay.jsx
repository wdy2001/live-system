import React from 'react'
import {
  Steps,
  Radio,
  Form,
  Input,
  Select,
  DatePicker,
  Button,
  Space,
  Descriptions,
  Table,
  Card,
  Result,
  message,
} from 'antd'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import { queryBill, payBill } from '@/api/payment'
import { utilityTypeLabel } from '@/utils/mapping'

const { Step } = Steps
const { Option } = Select

function Pay() {
  const navigate = useNavigate()
  const [current, setCurrent] = React.useState(0)
  const [loading, setLoading] = React.useState(false)
  const [bill, setBill] = React.useState(null)
  const [payResult, setPayResult] = React.useState(null)

  const [form1] = Form.useForm()
  const [form2] = Form.useForm()

  const typeValue = Form.useWatch('type', form1) || 'electric'

  const monthOptions = React.useMemo(() => {
    const arr = []
    const now = dayjs()
    for (let i = 0; i < 12; i++) {
      const m = now.subtract(i, 'month')
      arr.push({
        label: m.format('YYYY年MM月'),
        value: m.format('YYYY-MM'),
      })
    }
    return arr
  }, [])

  const next = () => setCurrent((c) => c + 1)
  const prev = () => setCurrent((c) => c - 1)

  const handleStep1Next = async () => {
    try {
      await form1.validateFields()
      next()
    } catch {}
  }

  const handleStep2Next = async () => {
    try {
      const values = await form2.validateFields()
      const type = form1.getFieldValue('type')
      setLoading(true)
      try {
        const data = await queryBill({
          utility_type: type,
          account_no: values.account_no,
          bill_month: values.bill_month,
        })
        setBill({
          ...data,
          utility_type: type,
          account_no: values.account_no,
          bill_month: values.bill_month,
        })
        next()
      } catch (e) {
      } finally {
        setLoading(false)
      }
    } catch {}
  }

  const handlePay = async () => {
    setLoading(true)
    try {
      const data = await payBill({
        utility_type: bill.utility_type,
        account_no: bill.account_no,
        bill_month: bill.bill_month,
      })
      setPayResult(data || {})
      next()
    } catch (e) {
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setCurrent(0)
    setBill(null)
    setPayResult(null)
    form1.resetFields()
    form2.resetFields()
  }

  const renderTierTable = () => {
    const tierItems = bill?.tier_items || bill?.tierDetails || []
    const dataSource = tierItems.map((t, idx) => ({
      key: idx,
      tier_label: t.tier_label || t.label || `第${idx + 1}档`,
      start: t.start,
      end: t.end,
      usage: t.usage,
      unit_price: t.unit_price,
      subtotal: t.subtotal,
    }))
    const columns = [
      { title: '档位', dataIndex: 'tier_label', key: 'tier_label' },
      {
        title: '用量区间',
        key: 'range',
        render: (_, r) =>
          r.start !== undefined && r.end !== undefined
            ? `${r.start} ~ ${r.end}`
            : r.end === null || r.end === undefined
            ? `≥ ${r.start}`
            : '-',
      },
      { title: '本档用量', dataIndex: 'usage', key: 'usage' },
      {
        title: '单价(元)',
        dataIndex: 'unit_price',
        key: 'unit_price',
        render: (v) => (typeof v === 'number' ? v.toFixed(2) : v),
      },
      {
        title: '小计(元)',
        dataIndex: 'subtotal',
        key: 'subtotal',
        render: (v) => (typeof v === 'number' ? v.toFixed(2) : v),
      },
    ]
    return (
      <Table
        size="small"
        pagination={false}
        dataSource={dataSource}
        columns={columns}
        rowKey="key"
      />
    )
  }

  const renderExtraTable = () => {
    const extraItems = bill?.extra_items || bill?.extraFees || []
    const dataSource = extraItems.map((e, idx) => ({
      key: idx,
      name: e.name || e.label,
      rate: e.rate || e.unit_price,
      usage: e.usage,
      subtotal: e.subtotal,
    }))
    const columns = [
      { title: '附加费名称', dataIndex: 'name', key: 'name' },
      {
        title: '费率(元/单位)',
        dataIndex: 'rate',
        key: 'rate',
        render: (v) => (typeof v === 'number' ? v.toFixed(4) : v),
      },
      { title: '用量', dataIndex: 'usage', key: 'usage' },
      {
        title: '小计(元)',
        dataIndex: 'subtotal',
        key: 'subtotal',
        render: (v) => (typeof v === 'number' ? v.toFixed(2) : v),
      },
    ]
    return (
      <Table
        size="small"
        pagination={false}
        dataSource={dataSource}
        columns={columns}
        rowKey="key"
      />
    )
  }

  return (
    <div>
      <Card style={{ marginBottom: 24 }}>
        <Steps current={current} size="small">
          <Step title="选择类型" />
          <Step title="输入户号" />
          <Step title="确认缴费" />
          <Step title="缴费完成" />
        </Steps>
      </Card>

      <Card>
        {current === 0 && (
          <div>
            <Form
              form={form1}
              layout="vertical"
              initialValues={{ type: 'electric' }}
            >
              <Form.Item
                label="请选择缴费类型"
                name="type"
                rules={[{ required: true, message: '请选择缴费类型' }]}
              >
                <Radio.Group size="large">
                  <Radio.Button value="electric">💡 电费</Radio.Button>
                  <Radio.Button value="water">💧 水费</Radio.Button>
                  <Radio.Button value="gas">🔥 燃气费</Radio.Button>
                </Radio.Group>
              </Form.Item>
            </Form>
            <div style={{ textAlign: 'right', marginTop: 16 }}>
              <Button type="primary" onClick={handleStep1Next}>
                下一步
              </Button>
            </div>
          </div>
        )}

        {current === 1 && (
          <div>
            <Form form={form2} layout="vertical">
              <Form.Item
                label="户号"
                name="account_no"
                rules={[{ required: true, message: '请输入户号' }]}
                extra={`如 ${typeValue === 'electric' ? 'E100001' : typeValue === 'water' ? 'W200002' : 'G300003'}`}
              >
                <Input placeholder="请输入户号" size="large" />
              </Form.Item>
              <Form.Item
                label="缴费月份"
                name="bill_month"
                rules={[{ required: true, message: '请选择月份' }]}
                initialValue={dayjs().format('YYYY-MM')}
              >
                <Select size="large" placeholder="请选择月份">
                  {monthOptions.map((m) => (
                    <Option key={m.value} value={m.value}>
                      {m.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Form>
            <Space style={{ marginTop: 16 }}>
              <Button onClick={prev}>上一步</Button>
              <Button type="primary" onClick={handleStep2Next} loading={loading}>
                查询账单
              </Button>
            </Space>
          </div>
        )}

        {current === 2 && bill && (
          <div>
            <Descriptions
              title="账单信息"
              bordered
              column={2}
              size="small"
              style={{ marginBottom: 16 }}
            >
              <Descriptions.Item label="户号">
                {bill.account_no}
              </Descriptions.Item>
              <Descriptions.Item label="类型">
                {utilityTypeLabel[bill.utility_type] || bill.utility_type}
              </Descriptions.Item>
              <Descriptions.Item label="账单月份">
                {bill.bill_month}
              </Descriptions.Item>
              <Descriptions.Item label="应缴总金额">
                <span style={{ color: '#cf1322', fontWeight: 600, fontSize: 16 }}>
                  ¥ {(bill.total ?? 0).toFixed(2)}
                </span>
              </Descriptions.Item>
            </Descriptions>

            <Card title="阶梯用量明细" size="small" style={{ marginBottom: 12 }}>
              {renderTierTable()}
            </Card>
            <Card title="附加费明细" size="small" style={{ marginBottom: 16 }}>
              {renderExtraTable()}
            </Card>

            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="阶梯合计">
                ¥ {(bill.base_total ?? bill.total ?? 0).toFixed(2)}
              </Descriptions.Item>
              <Descriptions.Item label="附加费合计">
                ¥ {(bill.extra_fee ?? 0).toFixed(2)}
              </Descriptions.Item>
              <Descriptions.Item label="应缴总金额" span={2}>
                <span style={{ color: '#cf1322', fontWeight: 600, fontSize: 18 }}>
                  ¥ {(bill.total ?? 0).toFixed(2)}
                </span>
              </Descriptions.Item>
            </Descriptions>

            <Space style={{ marginTop: 24 }}>
              <Button onClick={prev}>上一步</Button>
              <Button type="primary" size="large" onClick={handlePay} loading={loading}>
                确认缴费
              </Button>
            </Space>
          </div>
        )}

        {current === 3 && (
          <Result
            status="success"
            title="缴费成功"
            subTitle={`已为户号 ${bill?.account_no} 完成缴费`}
            extra={[
              <Descriptions
                key="info"
                column={2}
                size="small"
                style={{ maxWidth: 520, margin: '0 auto 24px' }}
              >
                <Descriptions.Item label="订单号">
                  {payResult?.order_no || payResult?.id || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="缴费金额">
                  ¥ {(payResult?.total ?? bill?.total ?? 0).toFixed(2)}
                </Descriptions.Item>
                <Descriptions.Item label="户号">
                  {bill?.account_no}
                </Descriptions.Item>
                <Descriptions.Item label="缴费时间">
                  {payResult?.paid_at
                    ? dayjs(payResult.paid_at).format('YYYY-MM-DD HH:mm:ss')
                    : dayjs().format('YYYY-MM-DD HH:mm:ss')}
                </Descriptions.Item>
              </Descriptions>,
              <Space key="btns">
                <Button onClick={handleReset}>继续缴费</Button>
                <Button type="primary" onClick={() => navigate('/records')}>
                  查看记录
                </Button>
              </Space>,
            ]}
          />
        )}
      </Card>
    </div>
  )
}

export default Pay
