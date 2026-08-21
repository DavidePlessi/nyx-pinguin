import { createRouter, createWebHistory } from 'vue-router'
import HomeDashboard from '../views/HomeDashboard.vue'
import Login from '../views/Login.vue'
import ManualView from '../views/ManualView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: HomeDashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/broadcasting',
      name: 'Broadcasting',
      component: () => import('../views/BroadcastingView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
    {
      path: '/manual',
      name: 'Manual',
      component: ManualView,
      meta: { requiresAuth: true }
    },
    {
      path: '/music',
      name: 'Music',
      component: () => import('../views/MusicView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/drops',
      name: 'Drops',
      component: () => import('../views/DropsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      name: 'AdminPanel',
      component: () => import('../views/AdminPanel.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/drops-admin',
      name: 'DropsAdmin',
      component: () => import('../views/DropsAdmin.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to) => {
  const isAuthenticated = !!localStorage.getItem('dab_session_token')

  if (to.meta.requiresAuth && !isAuthenticated) {
    // Redirect to login but keep query params (e.g. guild)
    return { name: 'Login', query: to.query }
  }
})

export default router
