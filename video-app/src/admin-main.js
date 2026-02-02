import { createApp } from 'vue'
import AdminApp from './AdminApp.vue'
import adminRouter from './router/admin'
import './assets/styles.css'

const app = createApp(AdminApp)
app.use(adminRouter)
app.mount('#app')
