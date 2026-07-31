export const utilityTypeLabel = {
  electric: '电费',
  water: '水费',
  gas: '燃气费',
}

export const utilityTypeColor = {
  electric: 'blue',
  water: 'green',
  gas: 'orange',
}

export const paymentStatusLabel = {
  unpaid: '待缴费',
  paid: '已缴费',
  overdue: '已欠费',
}

export const paymentStatusColor = {
  unpaid: 'orange',
  paid: 'green',
  overdue: 'red',
}

export const urgencyLabel = {
  low: '一般',
  middle: '紧急',
  high: '非常紧急',
}

export const urgencyColor = {
  low: 'blue',
  middle: 'orange',
  high: 'red',
}

export const repairStatusLabel = {
  pending: '待受理',
  processing: '处理中',
  completed: '已完成',
  cancelled: '已取消',
}

export const repairStatusColor = {
  pending: 'default',
  processing: 'processing',
  completed: 'success',
  cancelled: 'error',
}

export const repairTypeLabel = {
  electric_trip: '电路跳闸',
  electric_meter_fault: '电表故障',
  electric_leakage: '漏电',
  water_leak: '水管漏水',
  water_meter_abnormal: '水表异常',
  water_blockage: '堵塞',
  gas_leak: '燃气泄漏',
  gas_meter_fault: '燃气表故障',
  other: '其他',
}

export const repairTypeOptions = [
  { label: '电路跳闸', value: 'electric_trip' },
  { label: '电表故障', value: 'electric_meter_fault' },
  { label: '漏电', value: 'electric_leakage' },
  { label: '水管漏水', value: 'water_leak' },
  { label: '水表异常', value: 'water_meter_abnormal' },
  { label: '堵塞', value: 'water_blockage' },
  { label: '燃气泄漏', value: 'gas_leak' },
  { label: '燃气表故障', value: 'gas_meter_fault' },
  { label: '其他', value: 'other' },
]

export function getRepairCategory(type) {
  if (!type) return 'other'
  if (type.startsWith('electric_')) return 'electric'
  if (type.startsWith('water_')) return 'water'
  if (type.startsWith('gas_')) return 'gas'
  return 'other'
}

export const repairCategoryLabel = {
  electric: '电力',
  water: '水务',
  gas: '燃气',
  other: '其他',
}

export const repairCategoryColor = {
  electric: 'blue',
  water: 'cyan',
  gas: 'orange',
  other: 'default',
}
