<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formData = ref({
  usernameOrEmail: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

const login = async () => {
  if (!formData.value.usernameOrEmail || !formData.value.password) {
    error.value = 'Please enter all required fields'
    return
  }

  loading.value = true
  error.value = ''

  try {
    // Determine if input is username or email
    const isEmail = formData.value.usernameOrEmail.includes('@')
    
    const credentials = {
      password: formData.value.password
    }
    
    if (isEmail) {
      credentials.email = formData.value.usernameOrEmail
    } else {
      credentials.username = formData.value.usernameOrEmail
    }
    
    await authStore.login(credentials)
    
    // Redirect based on user role
    if (authStore.userRole === 'sponsor') {
      router.push('/sponsor/dashboard')
    } else if (authStore.userRole === 'influencer') {
      router.push('/influencer/dashboard')
    } else if (authStore.userRole === 'admin') {
      router.push('/admin/dashboard')
    } else {
      router.push('/')
    }
  } catch (err) {
    error.value = err.response?.data?.message || 'Login failed. Please check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page py-5">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-md-6 col-lg-5">
          <div class="card shadow border-0">
            <div class="card-body p-4 p-md-5">
              <h1 class="text-center mb-4">Log In</h1>
              
              <form @submit.prevent="login">
                <div class="mb-3">
                  <label for="usernameOrEmail" class="form-label">Username or Email</label>
                  <div class="input-group">
                    <span class="input-group-text">
                      <i class="bi bi-person"></i>
                    </span>
                    <input 
                      type="text" 
                      class="form-control" 
                      id="usernameOrEmail" 
                      v-model="formData.usernameOrEmail" 
                      placeholder="Enter username or email"
                      required
                    >
                  </div>
                </div>
                
                <div class="mb-3">
                  <label for="password" class="form-label">Password</label>
                  <div class="input-group">
                    <span class="input-group-text">
                      <i class="bi bi-lock"></i>
                    </span>
                    <input 
                      type="password" 
                      class="form-control" 
                      id="password" 
                      v-model="formData.password" 
                      placeholder="Enter password"
                      required
                    >
                  </div>
                </div>
                
                <div class="alert alert-danger" v-if="error">
                  {{ error }}
                </div>
                
                <div class="d-grid mb-4">
                  <button type="submit" class="btn btn-primary py-2" :disabled="loading">
                    <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
                    {{ loading ? 'Logging In...' : 'Log In' }}
                  </button>
                </div>
                
                <p class="text-center mb-0">
                  Don't have an account? 
                  <router-link to="/register" class="fw-bold text-decoration-none">Register</router-link>
                </p>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template> 