import { createRouter, createWebHistory } from 'vue-router'
import ProjectListView from '../views/ProjectListView.vue'
import ScriptView from '../views/ScriptView.vue'
import StoryboardView from '../views/StoryboardView.vue'
import CastingView from '../views/CastingView.vue'
import GalleryView from '../views/GalleryView.vue'
import AudioView from '../views/AudioView.vue'
import StudioView from '../views/StudioView.vue'
import ModelConfigView from '../views/ModelConfigView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/projects' },
    { path: '/projects', name: 'projects', component: ProjectListView },
    {
      path: '/projects/:id/script',
      name: 'script',
      component: ScriptView,
    },
    {
      path: '/projects/:id/storyboard',
      name: 'storyboard',
      component: StoryboardView,
    },
    {
      path: '/projects/:id/casting',
      name: 'casting',
      component: CastingView,
    },
    {
      path: '/projects/:id/gallery',
      name: 'gallery',
      component: GalleryView,
    },
    {
      path: '/projects/:id/audio',
      name: 'audio',
      component: AudioView,
    },
    {
      path: '/projects/:id/studio',
      name: 'studio',
      component: StudioView,
    },
    { path: '/settings/models', name: 'model-config', component: ModelConfigView },
  ],
})

export default router
