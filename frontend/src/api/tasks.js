import { http } from './http'

export const terminateTask = async (taskId) => {
  const url = `/api/task/${encodeURIComponent(taskId)}/terminate`
  const resp = await http.delete(url)
  return resp.data
}

export const batchTerminateTasks = async (taskIds) => {
  const resp = await http.post('/api/task/batch-terminate', { taskIds })
  return resp.data
}
