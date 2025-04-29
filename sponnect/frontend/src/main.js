import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import 'bootstrap-icons/font/bootstrap-icons.css'
import './assets/main.css'
import './assets/master.css'

// Set Indian locale for internationalization
const indiaLocale = 'en-IN';
try {
  // Configure Intl formatters for consistent formatting across the app
  if (Intl && Intl.DateTimeFormat) {
    // Register India locale
    Intl.DateTimeFormat(indiaLocale, {
      timeZone: 'Asia/Kolkata',
      hour12: true
    });
    
    console.log('Indian locale and timezone set successfully');
  }
} catch (e) {
  console.error('Error setting Indian locale:', e);
}

const app = createApp(App)

// Global error handler
app.config.errorHandler = (err, vm, info) => {
  console.error('Global error:', err);
  console.error('Vue instance:', vm);
  console.error('Error info:', info);
  
  // Here you could also send errors to a monitoring service like Sentry
  // or display a global error notification
}

// Register global properties
app.config.globalProperties.$currencySymbol = '₹';
app.config.globalProperties.$timezone = 'IST';

app.use(createPinia())
app.use(router)

app.mount('#app')
