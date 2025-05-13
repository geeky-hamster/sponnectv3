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

// Ensure Bootstrap's JavaScript is properly initialized
document.addEventListener('DOMContentLoaded', () => {
  // Initialize all dropdowns
  if (typeof bootstrap !== 'undefined') {
    // Initialize all tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Initialize all popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    
    console.log('Bootstrap components initialized');
  } else {
    console.warn('Bootstrap JS not loaded properly');
  }
});

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

// Add a global mixin for app-wide dropdown initialization
app.mixin({
  mounted() {
    // This will run on every component that's mounted
    this.$nextTick(() => {
      // Initialize dropdowns in this component
      if (typeof bootstrap !== 'undefined') {
        const dropdowns = this.$el.querySelectorAll('.dropdown-toggle');
        if (dropdowns.length > 0) {
          [...dropdowns].forEach(el => {
            // Only initialize if not already initialized
            if (!bootstrap.Dropdown.getInstance(el)) {
              new bootstrap.Dropdown(el);
            }
          });
        }
      }
    });
  }
})

app.mount('#app')
