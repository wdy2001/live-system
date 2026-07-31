import React from 'react'
import { Card, Row, Col, Statistic, Button, Space } from 'antd'
import {
  PayCircleOutlined,
  UnorderedListOutlined,
  InfoCircleOutlined,
  ToolOutlined,
  RiseOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const featureCards = [
  {
    title: '在线缴费',
    desc: '电费、水费、燃气费一键缴纳',
    icon: <PayCircleOutlined style={{ fontSize: 36, color: '#1677ff' }} />,
    path: '/pay',
    color: '#e6f4ff',
  },
  {
    title: '缴费记录',
    desc: '查看历史缴费订单与详情',
    icon: <UnorderedListOutlined style={{ fontSize: 36, color: '#52c41a' }} />,
    path: '/records',
    color: '#f6ffed',
  },
  {
    title: '计费规则',
    desc: '阶梯电价、水价、燃气费说明',
    icon: <InfoCircleOutlined style={{ fontSize: 36, color: '#fa8c16' }} />,
    path: '/rules',
    color: '#fff7e6',
  },
  {
    title: '故障报修',
    desc: '水电燃气故障在线报修追踪',
    icon: <ToolOutlined style={{ fontSize: 36, color: '#722ed1' }} />,
    path: '/repair',
    color: '#f9f0ff',
  },
]

function Home() {
  const navigate = useNavigate()
  return (
    <div>
      <Card
        style={{ marginBottom: 24, borderRadius: 8 }}
        bodyStyle={{ padding: 32 }}
      >
        <h1 style={{ margin: 0, fontSize: 26, marginBottom: 8 }}>
          欢迎使用生活缴费系统
        </h1>
        <p style={{ margin: 0, color: '#666', fontSize: 14 }}>
          一站式处理您的电费、水费、燃气费，账单查询、在线缴费、故障报修一键搞定
        </p>
      </Card>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="近30天缴费笔数"
              value={0}
              suffix="笔"
              prefix={<RiseOutlined style={{ color: '#1677ff' }} />}
              valueStyle={{ color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="累计缴费金额"
              value={0}
              precision={2}
              prefix="¥"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="报修进行中"
              value={0}
              suffix="单"
              prefix={<ClockCircleOutlined style={{ color: '#fa8c16' }} />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {featureCards.map((item) => (
          <Col xs={24} sm={12} lg={6} key={item.path}>
            <Card
              hoverable
              onClick={() => navigate(item.path)}
              bodyStyle={{ padding: 24 }}
              style={{ height: '100%' }}
            >
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 12,
                  background: item.color,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: 16,
                }}
              >
                {item.icon}
              </div>
              <h3 style={{ margin: 0, marginBottom: 6 }}>{item.title}</h3>
              <p
                style={{
                  margin: 0,
                  color: '#888',
                  fontSize: 13,
                  marginBottom: 16,
                  minHeight: 40,
                }}
              >
                {item.desc}
              </p>
              <Button type="link" style={{ padding: 0 }}>
                立即进入 &rarr;
              </Button>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  )
}

export default Home
