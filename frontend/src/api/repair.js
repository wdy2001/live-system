import request from './request'

export function createRepair(data) {
  return request({
    url: '/repairs',
    method: 'post',
    data,
  })
}

export function listRepairs(params) {
  return request({
    url: '/repairs',
    method: 'get',
    params,
  })
}

export function getRepair(id) {
  return request({
    url: `/repairs/${id}`,
    method: 'get',
  })
}

export function cancelRepair(id) {
  return request({
    url: `/repairs/${id}/cancel`,
    method: 'post',
  })
}

export function debugTransitionRepair(id, nextStatus) {
  return request({
    url: `/repairs/${id}/debug-transition`,
    method: 'post',
    data: { next_status: nextStatus },
  })
}
