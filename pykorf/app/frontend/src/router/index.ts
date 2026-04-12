import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'file-picker',
      component: () => import('../views/FilePickerView.vue'),
    },
    {
      path: '/model',
      name: 'main-menu',
      component: () => import('../views/MainMenuView.vue'),
    },
    {
      path: '/model/data',
      name: 'apply-data',
      component: () => import('../views/ApplyDataView.vue'),
    },
    {
      path: '/model/settings',
      name: 'global-parameters',
      component: () => import('../views/GlobalParametersView.vue'),
    },
    {
      path: '/model/bulk-copy',
      name: 'bulk-copy',
      component: () => import('../views/BulkCopyView.vue'),
    },
    {
      path: '/model/report',
      name: 'report',
      component: () => import('../views/ReportView.vue'),
    },
    {
      path: '/model/pipe-criteria',
      name: 'pipe-criteria',
      component: () => import('../views/PipeCriteriaView.vue'),
    },
    {
      path: '/model/references',
      name: 'references',
      component: () => import('../views/ReferencesView.vue'),
    },
    {
      path: '/preferences',
      name: 'preferences',
      component: () => import('../views/PreferencesView.vue'),
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
  ],
})

/**
 * Navigation guard: Redirect to file picker if no model is loaded.
 * Only applies to routes that require an active model session.
 * The /preferences and /about pages are accessible without a model.
 */
const MODEL_REQUIRED_ROUTES = new Set([
  'main-menu', 'apply-data', 'global-parameters', 'bulk-copy',
  'report', 'pipe-criteria', 'references',
])

router.beforeEach(async (to) => {
  if (!MODEL_REQUIRED_ROUTES.has(to.name as string)) return true

  // Lazy import to avoid circular dependency at module init time
  const { useSessionStore } = await import('../stores/session')
  const session = useSessionStore()

  // Fetch latest status if we haven't yet
  if (!session.modelLoaded && session.recentFiles.length === 0) {
    await session.fetchStatus()
  }

  if (!session.isLoaded) {
    return { name: 'file-picker', replace: true }
  }
  return true
})

export default router
