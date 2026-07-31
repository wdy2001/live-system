import request from './request'

export function getBillingRules(type) {
  return request({
    url: '/billing-rules',
    method: 'get',
    params: { type },
  })
}

export function getMeterUsage(params) {
  return request({
    url: '/meter-usages',
    method: 'get',
    params,
  })
}
