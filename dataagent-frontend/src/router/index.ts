import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/',
    component: () => import('@/layout/index.vue'),
    redirect: '/workspace',
    children: [
      {
        path: 'workspace',
        name: 'Workspace',
        component: () => import('@/views/workspace/index.vue'),
        meta: { title: '工作台' },
      },
      {
        path: 'agents',
        name: 'AgentList',
        component: () => import('@/views/agent/list.vue'),
        meta: { title: 'Agent管理' },
      },
      {
        path: 'agents/:id',
        name: 'AgentDetail',
        component: () => import('@/views/agent/detail.vue'),
        meta: { title: 'Agent详情' },
      },
      {
        path: 'agents/:id/config',
        name: 'AgentConfig',
        component: () => import('@/views/agent/config.vue'),
        meta: { title: 'Agent配置' },
      },
      {
        path: 'agents/:id/chat',
        name: 'AgentChat',
        component: () => import('@/views/chat/index.vue'),
        meta: { title: '对话调试' },
      },
      {
        path: 'resources',
        name: 'ResourceList',
        component: () => import('@/views/resource/list.vue'),
        meta: { title: '资源管理' },
      },
      {
        path: 'resources/:type/:id',
        name: 'ResourceDetail',
        component: () => import('@/views/resource/detail.vue'),
        meta: { title: '资源详情' },
      },
      {
        path: 'evaluation',
        name: 'Evaluation',
        component: () => import('@/views/evaluation/index.vue'),
        meta: { title: '评测中心' },
      },
      {
        path: 'evaluation/report/:taskId',
        name: 'EvalReport',
        component: () => import('@/views/evaluation/report.vue'),
        meta: { title: '评测报告' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/workspace',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局前置守卫
router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()

  // 不需要登录的页面
  if (to.meta.public) {
    next()
    return
  }

  // 需要登录但未登录，跳转登录页
  if (!userStore.isLoggedIn) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  next()
})

// 设置页面标题
router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  if (title) {
    document.title = `${title} - DataAgent平台`
  } else {
    document.title = 'DataAgent平台'
  }
})

export default router