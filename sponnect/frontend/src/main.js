import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import 'bootstrap-icons/font/bootstrap-icons.css'
import './assets/main.css'

const app = createApp(App)

// Global error handler
app.config.errorHandler = (err, vm, info) => {
  console.error('Global error:', err);
  console.error('Vue instance:', vm);
  console.error('Error info:', info);
  
  // Here you could also send errors to a monitoring service like Sentry
  // or display a global error notification
}

app.use(createPinia())
app.use(router)

app.mount('#app')
