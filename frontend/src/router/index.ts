import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    {
      path: '/dashboard',
      component: () => import('@/pages/Dashboard/index.vue'),
    },
    {
      path: '/workflow/:projectId?',
      component: () => import('@/pages/Workflow/index.vue'),
    },
    {
      path: '/agents',
      component: () => import('@/pages/Agent/index.vue'),
    },
    {
      path: '/project/:projectId?',
      component: () => import('@/pages/Project/index.vue'),
    },
    {
      path: '/git/:projectId?',
      component: () => import('@/pages/Git/index.vue'),
    },
    {
      path: '/deployment/:projectId?',
      component: () => import('@/pages/Deployment/index.vue'),
    },
    {
      path: '/operations/:projectId?',
      component: () => import('@/pages/Operations/index.vue'),
    },
    {
      path: '/knowledge',
      component: () => import('@/pages/Knowledge/index.vue'),
    },
    {
      path: '/organization',
      component: () => import('@/pages/Organization/index.vue'),
    },
    {
      path: '/settings',
      component: () => import('@/pages/Settings/index.vue'),
    },
  ],
})

export default router
