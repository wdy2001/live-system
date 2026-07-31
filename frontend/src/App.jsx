import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from '@/layouts/MainLayout.jsx'
import Home from '@/pages/Home.jsx'
import Login from '@/pages/Login.jsx'
import Register from '@/pages/Register.jsx'
import NotFound from '@/pages/NotFound.jsx'
import Pay from '@/pages/Pay.jsx'
import Records from '@/pages/Records.jsx'
import Rules from '@/pages/Rules.jsx'
import RepairCreate from '@/pages/RepairCreate.jsx'
import RepairList from '@/pages/RepairList.jsx'
import Profile from '@/pages/Profile.jsx'
import { isLoggedIn } from '@/utils/auth'

function RequireAuth({ children }) {
  if (!isLoggedIn()) {
    return <Navigate to="/login" replace />
  }
  return children
}

function GuestOnly({ children }) {
  if (isLoggedIn()) {
    return <Navigate to="/" replace />
  }
  return children
}

function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <GuestOnly>
            <Login />
          </GuestOnly>
        }
      />
      <Route
        path="/register"
        element={
          <GuestOnly>
            <Register />
          </GuestOnly>
        }
      />
      <Route
        path="/"
        element={
          <RequireAuth>
            <MainLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Home />} />
        <Route path="pay" element={<Pay />} />
        <Route path="records" element={<Records />} />
        <Route path="rules" element={<Rules />} />
        <Route path="repair" element={<RepairCreate />} />
        <Route path="repair/list" element={<RepairList />} />
        <Route path="profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default App
