import axios from 'axios'

export function getClient() {
  const token = localStorage.getItem('ams_token') || ''
  return axios.create({
    baseURL: '/api/v1',
    headers: { Authorization: `Bearer ${token}` },
  })
}
