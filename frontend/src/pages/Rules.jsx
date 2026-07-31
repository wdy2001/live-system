import React from 'react'
import { Tabs, Table, Card, Row, Col, Tag, Spin, Empty } from 'antd'
import { getBillingRules } from '@/api/billing'

const unitMap = {
  electric: '度',
  water: 'm³',
  gas: 'm³',
}

const mockRules = {
  electric: {
    tiers: [
      { label: '第一档', start: 0, end: 240, unit_price: 0.5283 },
      { label: '第二档', start: 240, end: 400, unit_price: 0.5783 },
      { label: '第三档', start: 400, end: null, unit_price: 0.8283 },
    ],
    extras: [
      { name: '城市公共事业附加费', rate: 0.015, remark: '按实际用电量收取' },
      { name: '水库移民扶持资金', rate: 0.0062, remark: '按实际用电量收取' },
    ],
  },
  water: {
    tiers: [
      { label: '第一档', start: 0, end: 15, unit_price: 3.5 },
      { label: '第二档', start: 15, end: 25, unit_price: 5.25 },
      { label: '第三档', start: 25, end: null, unit_price: 8.75 },
    ],
    extras: [
      { name: '污水处理费', rate: 1.2, remark: '按用水量收取' },
      { name: '水资源费', rate: 0.3, remark: '按用水量收取' },
    ],
  },
  gas: {
    tiers: [
      { label: '第一档', start: 0, end: 310, unit_price: 2.63 },
      { label: '第二档', start: 310, end: 500, unit_price: 3.15 },
      { label: '第三档', start: 500, end: null, unit_price: 3.94 },
    ],
    extras: [
      { name: '燃气安全保险费', rate: 0.02, remark: '按用气量收取，可选' },
    ],
  },
}

function RuleTab({ type }) {
  const [loading, setLoading] = React.useState(false)
  const [rules, setRules] = React.useState(null)

  React.useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      try {
        const data = await getBillingRules(type)
        if (!cancelled) setRules(data || mockRules[type])
      } catch {
        if (!cancelled) setRules(mockRules[type])
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [type])

  const unit = unitMap[type]
  const tiers = rules?.tiers || rules?.tier_rules || []
  const extras = rules?.extras || rules?.extra_fees || []

  const tierColumns = [
    { title: '档位', dataIndex: 'label', key: 'label', render: (v, r, i) => v || r.tier_label || `第${i + 1}档` },
    {
      title: `月用量区间（${unit}）`,
      key: 'range',
      render: (_, r) => {
        const s = r.start ?? r.start_usage
        const e = r.end ?? r.end_usage
        if (e === null || e === undefined) return `${s}${unit} 以上`
        return `${s} ~ ${e} ${unit}`
      },
    },
    {
      title: `单价（元/${unit}）`,
      dataIndex: 'unit_price',
      key: 'p',
      render: (v, r) => {
        const val = v !== undefined ? v : r.price
        return typeof val === 'number' ? val.toFixed(4) : val
      },
    },
  ]

  return (
    <Spin spinning={loading}>
      {rules ? (
        <div>
          <Card
            title={`阶梯计费（${type === 'electric' ? '电价' : type === 'water' ? '水价' : '燃气价格'}）`}
            style={{ marginBottom: 16 }}
          >
            {tiers.length ? (
              <Table
                size="middle"
                pagination={false}
                rowKey={(r, i) => i}
                dataSource={tiers}
                columns={tierColumns}
              />
            ) : (
              <Empty description="暂无阶梯数据" />
            )}
          </Card>
          <Card title="附加费说明">
            {extras.length ? (
              <Row gutter={[16, 16]}>
                {extras.map((e, i) => (
                  <Col xs={24} md={12} key={i}>
                    <Card size="small" type="inner" title={
                      <Tag color="purple" style={{ marginRight: 8 }}>
                        附加费
                      </Tag>
                    }>
                      <div style={{ marginBottom: 8 }}>
                        <b>费率：</b>
                        {typeof e.rate === 'number'
                          ? `${e.rate.toFixed(4)} 元/${unit}`
                          : e.rate || '-'}
                      </div>
                      <div style={{ color: '#666' }}>
                        <b>备注：</b>
                        {e.remark || e.note || '无'}
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            ) : (
              <Empty description="暂无附加费" />
            )}
          </Card>
        </div>
      ) : null}
    </Spin>
  )
}

function Rules() {
  return (
    <Card>
      <Tabs
        defaultActiveKey="electric"
        size="large"
        items={[
          { key: 'electric', label: '💡 电费规则', children: <RuleTab type="electric" /> },
          { key: 'water', label: '💧 水费规则', children: <RuleTab type="water" /> },
          { key: 'gas', label: '🔥 燃气费规则', children: <RuleTab type="gas" /> },
        ]}
      />
    </Card>
  )
}

export default Rules
