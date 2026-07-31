import request from './request'

export function queryBill(data) {
  return request({
    url: '/payments/query',
    method: 'post',
    data,
  })
}

export function payBill(data) {
  return request({
    url: '/payments/pay',
    method: 'post',
    data,
  })
}

export function getPaymentOrder(id) {
  return request({
    url: `/payments/${id}`,
    method: 'get',
  })
}

export function listPayments(params) {
  return request({
    url: '/payments',
    method: 'get',
    params,
  })
}
