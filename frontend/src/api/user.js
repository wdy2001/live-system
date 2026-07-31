import request from './request'

export function getMe() {
  return request({
    url: '/users/me',
    method: 'get',
  })
}

export function updateMe(data) {
  return request({
    url: '/users/me',
    method: 'put',
    data,
  })
}
