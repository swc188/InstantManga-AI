import { defineStore } from 'pinia'
import { ref } from 'vue'
import { request } from '../api/client'

export interface Project {
  id: number
  title: string
  genre?: string
  status: string
  created_at: string
  updated_at: string
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const loading = ref(false)

  async function fetchProjects() {
    loading.value = true
    try {
      projects.value = await request<Project[]>('/projects')
    } finally {
      loading.value = false
    }
  }

  async function loadProject(id: number) {
    currentProject.value = await request<Project>(`/projects/${id}`)
  }

  async function createProject(payload: { title: string; genre?: string }) {
    const project = await request<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    projects.value.push(project)
    currentProject.value = project
    return project
  }

  return {
    projects,
    currentProject,
    loading,
    fetchProjects,
    loadProject,
    createProject,
  }
})
