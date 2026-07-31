import React from 'react'
import {
  Tabs,
  Table,
  Tag,
  Button,
  Space,
  Drawer,
  Descriptions,
  Timeline,
  Popconfirm,
  message,
  Spin,
} from 'antd'
import dayjs from 'dayjs'
import { listRepairs, getRepair, cancelRepair } from '@/api/repair'
import {
  repairTypeLabel,
  urgencyLabel,
  urgencyColor,
  repairStatusLabel,
  repairStatusColor,
  getRepairCategory,
  repairCategoryLabel,
  repairCategoryColor,
} from '@/utils/mapping'

function RepairList() {
  const [activeKey, setActiveKey] = React.useState('all')
  const [loading, setLoading] = React.useState(false)
  const [data, setData] = React.useState([])
  const [pagination, setPagination] = React.useState({ current: 1, pageSize: 10 })
  const [total, setTotal] = React.useState(0)
  const [detailId, setDetailId] = React.useState(null)
  const [detail, setDetail] = React.useState(null)
  const [detailLoading, setDetailLoading] = React.useState(false)

  const fetchList = React.useCallback(async () => {
    setLoading(true)
    try {
      const params = {
        page: pagination.current,
        page_size: pagination.pageSize,
      }
      if (activeKey !== 'all') {
        params.status = activeKey
      }
      const res = await listRepairs(params)
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
  }, [activeKey, pagination])

  React.useEffect(() => {
    fetchList()
  }, [fetchList])

  const handleCancel = async (record) => {
    try {
      await cancelRepair(record.id)
      message.success('已取消报修')
      fetchList()
    } catch (e) {}
  }

  const handleOpenDetail = async (record) => {
    setDetailId(record.id)
    setDetail(null)
    setDetailLoading(true)
    try {
      let d = record
      try {
        const fetched = await getRepair(record.id)
        if (fetched) d = { ...record, ...fetched }
      } catch {}
      setDetail(d)
    } finally {
      setDetailLoading(false)
    }
  }

  const columns = [
    {
      title: '工单号',
      dataIndex: 'id',
      key: 'id',
      render: (v, r) => v || r.order_no || '-',
      width: 180,
    },
    {
      title: '报修类型',
      dataIndex: 'repair_type',
      key: 'repair_type',
      render: (v) => repairTypeLabel[v] || v || '-',
    },
    {
      title: '分类',
      key: 'category',
      render: (_, r) => {
        const c = getRepairCategory(r.repair_type)
        return (
          <Tag color={repairCategoryColor[c]}>
            {repairCategoryLabel[c]}
          </Tag>
        )
      },
    },
    {
      title: '紧急程度',
      dataIndex: 'urgency',
      key: 'urgency',
      render: (v) => (
        <Tag color={urgencyColor[v]}>{urgencyLabel[v] || v}</Tag>
      ),
    },
    {
      title: '地址',
      dataIndex: 'address',
      key: 'address',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (v) => (
        <Tag color={repairStatusColor[v]}>
          {repairStatusLabel[v] || v}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (v) => (v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-'),
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 160,
      render: (_, r) => (
        <Space>
          <Button type="link" size="small" onClick={() => handleOpenDetail(r)}>
            详情
          </Button>
          {r.status === 'pending' && (
            <Popconfirm
              title="确认取消该报修？"
              onConfirm={() => handleCancel(r)}
              okText="确认"
              cancelText="取消"
            >
              <Button type="link" size="small" danger>
                取消
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  const renderTimeline = (detailObj) => {
    const timeline = detailObj?.progress_timeline || detailObj?.timeline || []
    if (!timeline || timeline.length === 0) {
      const defaultItems = []
      if (detailObj?.created_at) {
        defaultItems.push({
          status: 'submitted',
          time: detailObj.created_at,
          note: '用户提交报修申请',
          color: 'blue',
        })
      }
      if (detailObj?.status === 'processing') {
        defaultItems.push({
          status: 'processing',
          time: detailObj.updated_at || new Date(),
          note: '工程师已出发',
          color: 'cyan',
        })
      }
      if (detailObj?.status === 'completed') {
        defaultItems.push({
          status: 'completed',
          time: detailObj.updated_at || new Date(),
          note: '维修完成并验收',
          color: 'green',
        })
      }
      if (detailObj?.status === 'cancelled') {
        defaultItems.push({
          status: 'cancelled',
          time: detailObj.updated_at || new Date(),
          note: '用户取消报修',
          color: 'red',
        })
      }
      if (defaultItems.length === 0) {
        return <p style={{ color: '#999' }}>暂无进度记录</p>
      }
      return (
        <Timeline
          items={defaultItems.map((t) => ({
            color: t.color,
            children: (
              <div>
                <div style={{ fontWeight: 600 }}>{t.note}</div>
                <div style={{ color: '#999', fontSize: 12 }}>
                  {t.time ? dayjs(t.time).format('YYYY-MM-DD HH:mm:ss') : ''}
                </div>
              </div>
            ),
          }))}
        />
      )
    }
    return (
      <Timeline
        items={timeline.map((t) => ({
          color:
            t.status === 'completed'
              ? 'green'
              : t.status === 'cancelled'
              ? 'red'
              : t.status === 'processing'
              ? 'cyan'
              : 'blue',
          children: (
            <div>
              <div style={{ fontWeight: 600 }}>
                {t.note || t.status || '进度更新'}
              </div>
              <div style={{ color: '#999', fontSize: 12 }}>
                {t.time ? dayjs(t.time).format('YYYY-MM-DD HH:mm:ss') : ''}
              </div>
            </div>
          ),
        }))}
      />
    )
  }

  return (
    <div>
      <Card>
        <Tabs
          activeKey={activeKey}
          onChange={(k) => {
            setActiveKey(k)
            setPagination((p) => ({ ...p, current: 1 }))
          }}
          items={[
            { key: 'all', label: `全部` },
            { key: 'pending', label: `待受理` },
            { key: 'processing', label: `处理中` },
            { key: 'completed', label: `已完成` },
            { key: 'cancelled', label: `已取消` },
          ]}
        />
        <Table
          rowKey="id"
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

      <Drawer
        title="报修详情"
        placement="right"
        width={520}
        open={!!detailId}
        onClose={() => {
          setDetailId(null)
          setDetail(null)
        }}
        destroyOnClose
      >
        <Spin spinning={detailLoading}>
          {detail && (
            <div>
              <Descriptions title="基础信息" bordered size="small" column={1} style={{ marginBottom: 20 }}>
                <Descriptions.Item label="工单号">
                  {detail.id || detail.order_no || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="报修类型">
                  {repairTypeLabel[detail.repair_type] || detail.repair_type || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="分类">
                  {(() => {
                    const c = getRepairCategory(detail.repair_type)
                    return (
                      <Tag color={repairCategoryColor[c]}>
                        {repairCategoryLabel[c]}
                      </Tag>
                    )
                  })()}
                </Descriptions.Item>
                <Descriptions.Item label="紧急程度">
                  <Tag color={urgencyColor[detail.urgency]}>
                    {urgencyLabel[detail.urgency] || detail.urgency}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Tag color={repairStatusColor[detail.status]}>
                    {repairStatusLabel[detail.status] || detail.status}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="地址">
                  {detail.address || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="联系人">
                  {detail.contact || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="联系电话">
                  {detail.phone || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="问题描述">
                  {detail.description || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="创建时间">
                  {detail.created_at ? dayjs(detail.created_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
                </Descriptions.Item>
              </Descriptions>
              <h4 style={{ marginBottom: 12 }}>处理进度</h4>
              {renderTimeline(detail)}
            </div>
          )}
        </Spin>
      </Drawer>
    </div>
  )
}

export default RepairList
