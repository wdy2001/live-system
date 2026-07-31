import React from 'react'
import {
  Form,
  Select,
  DatePicker,
  Button,
  Space,
  Table,
  Tag,
  Modal,
  Descriptions,
  Card,
  message,
} from 'antd'
import dayjs from 'dayjs'
import { listPayments, getPaymentOrder } from '@/api/payment'
import {
  utilityTypeLabel,
  utilityTypeColor,
  paymentStatusLabel,
  paymentStatusColor,
} from '@/utils/mapping'

const { RangePicker } = DatePicker
const { Option } = Select

function Records() {
  const [form] = Form.useForm()
  const [loading, setLoading] = React.useState(false)
  const [data, setData] = React.useState([])
  const [total, setTotal] = React.useState(0)
  const [pagination, setPagination] = React.useState({ current: 1, pageSize: 10 })
  const [filters, setFilters] = React.useState({})
  const [detail, setDetail] = React.useState(null)
  const [detailLoading, setDetailLoading] = React.useState(false)

  const fetchList = React.useCallback(async () => {
    setLoading(true)
    try {
      const params = {
        ...filters,
        page: pagination.current,
        page_size: pagination.pageSize,
      }
      const res = await listPayments(params)
      const items = res?.items || res?.results || res?.list || res?.data || []
      const count = res?.total ?? res?.count ?? items.length
      setData(Array.isArray(items) ? items : [])
      setTotal(typeof count === 'number' ? count : items.length)
    } catch (e) {
      setData([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [filters, pagination])

  React.useEffect(() => {
    fetchList()
  }, [fetchList])

  const handleSearch = (values) => {
    const params = { ...values }
    if (params.type === 'all') delete params.type
    if (params.status === 'all') delete params.status
    if (params.date_range && params.date_range.length === 2) {
      params.start_date = dayjs(params.date_range[0]).format('YYYY-MM-DD')
      params.end_date = dayjs(params.date_range[1]).format('YYYY-MM-DD')
    }
    delete params.date_range
    setFilters(params)
    setPagination((p) => ({ ...p, current: 1 }))
  }

  const handleReset = () => {
    form.resetFields()
    setFilters({})
    setPagination({ current: 1, pageSize: 10 })
  }

  const handleViewDetail = async (record) => {
    setDetail(null)
    setDetailLoading(true)
    try {
      let d = record
      try {
        const fetched = await getPaymentOrder(record.id || record.order_no)
        if (fetched) d = { ...record, ...fetched }
      } catch {}
      setDetail(d)
    } finally {
      setDetailLoading(false)
    }
  }

  const columns = [
    {
      title: '订单号',
      dataIndex: 'order_no',
      key: 'order_no',
      render: (v, r) => v || r.id || '-',
      width: 180,
    },
    {
      title: '户号',
      dataIndex: 'account_no',
      key: 'account_no',
    },
    {
      title: '类型',
      dataIndex: 'utility_type',
      key: 'utility_type',
      render: (v) => (
        <Tag color={utilityTypeColor[v]} key={v}>
          {utilityTypeLabel[v] || v}
        </Tag>
      ),
    },
    {
      title: '月份',
      dataIndex: 'bill_month',
      key: 'bill_month',
    },
    {
      title: '总金额',
      dataIndex: 'total',
      key: 'total',
      render: (v) => (typeof v === 'number' ? `¥ ${v.toFixed(2)}` : v),
      align: 'right',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (v) => (
        <Tag color={paymentStatusColor[v]} key={v}>
          {paymentStatusLabel[v] || v}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v) => (v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-'),
      width: 170,
    },
    {
      title: '缴费时间',
      dataIndex: 'paid_at',
      key: 'paid_at',
      render: (v) => (v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-'),
      width: 170,
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 100,
      render: (_, r) => (
        <Button type="link" size="small" onClick={() => handleViewDetail(r)}>
          详情
        </Button>
      ),
    },
  ]

  const renderTierTable = (items) => {
    const arr = items || []
    const columns = [
      { title: '档位', dataIndex: 'tier_label', key: 't', render: (v, r, i) => v || r.label || `第${i + 1}档` },
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
      { title: '本档用量', dataIndex: 'usage', key: 'u' },
      { title: '单价(元)', dataIndex: 'unit_price', key: 'p', render: (v) => (typeof v === 'number' ? v.toFixed(2) : v) },
      { title: '小计(元)', dataIndex: 'subtotal', key: 's', render: (v) => (typeof v === 'number' ? v.toFixed(2) : v) },
    ]
    return (
      <Table size="small" pagination={false} dataSource={arr.map((x, i) => ({ ...x, key: i }))} columns={columns} />
    )
  }

  const renderExtraTable = (items) => {
    const arr = items || []
    const columns = [
      { title: '附加费名称', dataIndex: 'name', key: 'n', render: (v, r) => v || r.label || '-' },
      { title: '费率(元/单位)', dataIndex: 'rate', key: 'r', render: (v, r) => {
          const val = v !== undefined ? v : r.unit_price
          return typeof val === 'number' ? val.toFixed(4) : val
      } },
      { title: '用量', dataIndex: 'usage', key: 'u' },
      { title: '小计(元)', dataIndex: 'subtotal', key: 's', render: (v) => (typeof v === 'number' ? v.toFixed(2) : v) },
    ]
    return (
      <Table size="small" pagination={false} dataSource={arr.map((x, i) => ({ ...x, key: i }))} columns={columns} />
    )
  }

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Form
          form={form}
          layout="inline"
          onFinish={handleSearch}
          initialValues={{ type: 'all', status: 'all' }}
        >
          <Form.Item label="类型" name="type">
            <Select style={{ width: 140 }}>
              <Option value="all">全部</Option>
              <Option value="electric">电费</Option>
              <Option value="water">水费</Option>
              <Option value="gas">燃气费</Option>
            </Select>
          </Form.Item>
          <Form.Item label="状态" name="status">
            <Select style={{ width: 140 }}>
              <Option value="all">全部</Option>
              <Option value="unpaid">待缴费</Option>
              <Option value="paid">已缴费</Option>
              <Option value="overdue">已欠费</Option>
            </Select>
          </Form.Item>
          <Form.Item label="创建日期" name="date_range">
            <RangePicker />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                查询
              </Button>
              <Button onClick={handleReset}>重置</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card>
        <Table
          rowKey={(r) => r.id || r.order_no || Math.random()}
          loading={loading}
          dataSource={data}
          columns={columns}
          scroll={{ x: 1100 }}
          pagination={{
            ...pagination,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (t) => `共 ${t} 条`,
            onChange: (page, pageSize) =>
              setPagination({ current: page, pageSize }),
          }}
        />
      </Card>

      <Modal
        title="缴费订单详情"
        open={!!detail}
        onCancel={() => setDetail(null)}
        width={720}
        destroyOnClose
        confirmLoading={detailLoading}
        footer={[
          <Button key="close" onClick={() => setDetail(null)}>
            关闭
          </Button>,
        ]}
      >
        {detail && (
          <div>
            <Descriptions title="基础信息" bordered size="small" column={2} style={{ marginBottom: 16 }}>
              <Descriptions.Item label="订单号">
                {detail.order_no || detail.id || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={paymentStatusColor[detail.status]}>
                  {paymentStatusLabel[detail.status] || detail.status}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="户号">{detail.account_no}</Descriptions.Item>
              <Descriptions.Item label="类型">
                <Tag color={utilityTypeColor[detail.utility_type]}>
                  {utilityTypeLabel[detail.utility_type] || detail.utility_type}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="账单月份">{detail.bill_month}</Descriptions.Item>
              <Descriptions.Item label="总金额">
                <span style={{ color: '#cf1322', fontWeight: 600 }}>
                  ¥ {(detail.total ?? 0).toFixed(2)}
                </span>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {detail.created_at ? dayjs(detail.created_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="缴费时间">
                {detail.paid_at ? dayjs(detail.paid_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
              </Descriptions.Item>
            </Descriptions>
            <Card title="阶梯明细" size="small" style={{ marginBottom: 12 }}>
              {renderTierTable(detail.tier_items || detail.tierDetails)}
            </Card>
            <Card title="附加费明细" size="small">
              {renderExtraTable(detail.extra_items || detail.extraFees)}
            </Card>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Records
