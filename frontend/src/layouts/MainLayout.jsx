import React from 'react'
import { Layout, Menu, Dropdown, Avatar, Space, theme } from 'antd'
import {
  HomeOutlined,
  PayCircleOutlined,
  UnorderedListOutlined,
  InfoCircleOutlined,
  ToolOutlined,
  UserOutlined,
  LogoutOutlined,
  ProfileOutlined,
  FormOutlined,
  ListOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import { clearToken, getUser } from '@/utils/auth'

const { Header, Sider, Content } = Layout

function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = React.useState(false)
  const {
    token: { colorBgContainer },
  } = theme.useToken()

  const user = getUser() || {}
  const username = user.username || user.name || '用户'

  const selectedKeys = React.useMemo(() => {
    const path = location.pathname
    if (path.startsWith('/repair/list')) return ['/repair/list']
    if (path.startsWith('/repair')) return ['/repair']
    return [path]
  }, [location.pathname])

  const openKeys = React.useMemo(() => {
    if (location.pathname.startsWith('/repair')) return ['repair']
    return []
  }, [location.pathname])

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: '首页',
      onClick: () => navigate('/'),
    },
    {
      key: '/pay',
      icon: <PayCircleOutlined />,
      label: '在线缴费',
      onClick: () => navigate('/pay'),
    },
    {
      key: '/records',
      icon: <UnorderedListOutlined />,
      label: '缴费记录',
      onClick: () => navigate('/records'),
    },
    {
      key: '/rules',
      icon: <InfoCircleOutlined />,
      label: '计费规则',
      onClick: () => navigate('/rules'),
    },
    {
      key: 'repair',
      icon: <ToolOutlined />,
      label: '故障报修',
      children: [
        {
          key: '/repair',
          icon: <FormOutlined />,
          label: '提交报修',
          onClick: () => navigate('/repair'),
        },
        {
          key: '/repair/list',
          icon: <ListOutlined />,
          label: '报修进度',
          onClick: () => navigate('/repair/list'),
        },
      ],
    },
    {
      key: '/profile',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => navigate('/profile'),
    },
  ]

  const handleLogout = () => {
    clearToken()
    navigate('/login', { replace: true })
  }

  const userMenu = {
    items: [
      {
        key: 'profile',
        icon: <ProfileOutlined />,
        label: '我的资料',
        onClick: () => navigate('/profile'),
      },
      { type: 'divider' },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
        onClick: handleLogout,
      },
    ],
  }

  const pageTitle = React.useMemo(() => {
    const path = location.pathname
    const titles = {
      '/': '首页',
      '/pay': '在线缴费',
      '/records': '缴费记录',
      '/rules': '计费规则',
      '/repair': '提交报修',
      '/repair/list': '报修进度',
      '/profile': '个人中心',
    }
    return titles[path] || '生活缴费系统'
  }, [location.pathname])

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        width={220}
      >
        <div
          style={{
            height: 64,
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: collapsed ? 16 : 18,
            fontWeight: 600,
            letterSpacing: 1,
            background: 'rgba(255,255,255,0.04)',
            userSelect: 'none',
          }}
        >
          {collapsed ? '缴费' : '生活缴费系统'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={selectedKeys}
          defaultOpenKeys={openKeys}
          items={menuItems}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <h2 style={{ margin: 0, fontSize: 18 }}>{pageTitle}</h2>
          <Dropdown menu={userMenu} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar style={{ backgroundColor: '#1677ff' }} icon={<UserOutlined />} />
              <span style={{ color: '#333' }}>{username}</span>
            </Space>
          </Dropdown>
        </Header>
        <Content
          style={{
            margin: 24,
            padding: 24,
            background: colorBgContainer,
            borderRadius: 8,
            minHeight: 280,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout
