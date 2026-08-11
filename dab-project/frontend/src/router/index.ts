import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Login from '../views/Login.vue'
import ManualView from '../views/ManualView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: Dashboard,
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
    }
  ]
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('dab_session_token')

  if (to.meta.requiresAuth && !isAuthenticated) {
    // Redirect to login but keep query params (e.g. guild)
    next({ name: 'Login', query: to.query })
  } else {
    next()
  }
})

export default router
