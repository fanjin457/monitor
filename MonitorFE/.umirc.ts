export default {
  npmClient: 'pnpm',
  history: {
    type: 'hash'
  },
  routes: [
    {
      path: '/',
      redirect: 'main'
    },
    {
      path: '/login',
      component: 'login'
    },
    {
      path: '/main',
      component: 'main'
    }
  ]
};
