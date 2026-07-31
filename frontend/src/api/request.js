import axios from 'axios'
import { message } from 'antd'
import { getToken, clearToken } from '@/utils/auth'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

const request = axios.create({
  baseURL,
  timeout: 15000,
})

request.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res && typeof res === 'object' && 'code' in res) {
      if (res.code === 200 || res.code === 0 || res.code === 201) {
        return res.data !== undefined ? res.data : res
      }
      if (res.code === 401) {
        clearToken()
        if (typeof window !== 'undefined') {
          message.error('登录已过期')
          setTimeout(() => {
            window.location.href = '/login'
          }, 500)
        }
        return Promise.reject(new Error(res.message || '登录已过期'))
      }
      message.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  (error) => {
    if (error.response) {
      if (error.response.status === 401) {
        clearToken()
        message.error('登录已过期')
        setTimeout(() => {
          window.location.href = '/login'
        }, 500)
      } else if (error.response.status >= 500) {
        message.error('网络错误')
      } else {
        const res = error.response.data
        if (res && res.message) {
          message.error(res.message)
        } else {
          message.error('网络错误')
        }
      }
    } else {
      message.error('网络错误')
    }
    return Promise.reject(error)
  }
)

export default request
