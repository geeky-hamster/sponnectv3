<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formData = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'influencer', // Default to influencer
  
  // Sponsor-specific fields
  company_name: '',
  industry: '',
  
  // Influencer-specific fields
  influencer_name: '',
  category: '',
  niche: '',
  reach: null
})

// Category options for influencers
const categoryOptions = [
  'Fashion',
  'Beauty',
  'Fitness',
  'Travel',
  'Food',
  'Technology',
  'Gaming',
  'Lifestyle',
  'Business',
  'Education',
  'Entertainment',
  'Health',
  'Parenting',
  'Sports',
  'Other'
]

// Industry options for sponsors
const industryOptions = [
  'Technology',
  'Fashion',
  'Food & Beverage',
  'Health & Wellness',
  'Beauty',
  'Travel',
  'Financial Services',
  'Entertainment',
  'Retail',
  'Automotive',
  'Education',
  'Fitness',
  'Gaming',
  'Home & Decor',
  'Other'
]

const loading = ref(false)
const error = ref('')
const success = ref('')

const isSponsor = computed(() => formData.value.role === 'sponsor')
const isInfluencer = computed(() => formData.value.role === 'influencer')

const validateForm = () => {
  if (!formData.value.username || !formData.value.email || !formData.value.password) {
    error.value = 'Please fill in all required fields'
    return false
  }
  
  if (formData.value.password !== formData.value.confirmPassword) {
    error.value = 'Passwords do not match'
    return false
  }
  
  if (formData.value.role === 'sponsor' && !formData.value.company_name) {
    error.value = 'Company name is required for sponsors'
    return false
  }
  
  if (formData.value.role === 'influencer' && !formData.value.influencer_name) {
    error.value = 'Influencer name is required'
    return false
  }
  
  return true
}

const register = async () => {
  if (!validateForm()) return
  
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const userData = {
      username: formData.value.username,
      email: formData.value.email,
      password: formData.value.password,
      role: formData.value.role
    }
    
    // Add role-specific fields
    if (formData.value.role === 'sponsor') {
      userData.company_name = formData.value.company_name
      userData.industry = formData.value.industry
    } else {
      userData.influencer_name = formData.value.influencer_name
      userData.category = formData.value.category
      userData.niche = formData.value.niche
      userData.reach = formData.value.reach ? parseInt(formData.value.reach) : 0
    }
    
    await authStore.register(userData)
    
    // Show success message
    success.value = formData.value.role === 'sponsor' 
      ? 'Registration successful! Your sponsor account is pending approval.'
      : 'Registration successful! You can now log in to your influencer account.'
    
    // Clear form
    Object.keys(formData.value).forEach(key => {
      if (key !== 'role') formData.value[key] = key === 'reach' ? null : ''
    })
    
  } catch (err) {
    error.value = err.response?.data?.message || 'Registration failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-page py-5">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-md-10 col-lg-8">
          <div class="card shadow border-0">
            <div class="card-body p-4 p-md-5">
              <h1 class="text-center mb-4">Create an Account</h1>
              
              <div v-if="success" class="alert alert-success" role="alert">
                {{ success }}
                <div class="mt-2">
                  <router-link to="/login" class="btn btn-sm btn-success">Proceed to Login</router-link>
                </div>
              </div>
              
              <form v-else @submit.prevent="register">
                <!-- Role Selection -->
                <div class="mb-4 text-center">
                  <div class="btn-group" role="group">
                    <input type="radio" class="btn-check" name="role" id="sponsor" value="sponsor"
                           v-model="formData.role" autocomplete="off">
                    <label class="btn btn-outline-primary" for="sponsor">
                      <i class="bi bi-briefcase me-2"></i>I'm a Sponsor
                    </label>
                    
                    <input type="radio" class="btn-check" name="role" id="influencer" value="influencer"
                           v-model="formData.role" autocomplete="off">
                    <label class="btn btn-outline-primary" for="influencer">
                      <i class="bi bi-person-badge me-2"></i>I'm an Influencer
                    </label>
                  </div>
                </div>
                
                <!-- Common Fields -->
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label for="username" class="form-label">Username*</label>
                    <input 
                      type="text" 
                      class="form-control" 
                      id="username" 
                      v-model="formData.username" 
                      placeholder="Choose a username"
                      required
                    >
                  </div>
                  
                  <div class="col-md-6 mb-3">
                    <label for="email" class="form-label">Email*</label>
                    <input 
                      type="email" 
                      class="form-control" 
                      id="email" 
                      v-model="formData.email" 
                      placeholder="Enter your email"
                      required
                    >
                  </div>
                </div>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label for="password" class="form-label">Password*</label>
                    <input 
                      type="password" 
                      class="form-control" 
                      id="password" 
                      v-model="formData.password" 
                      placeholder="Create a password"
                      required
                    >
                  </div>
                  
                  <div class="col-md-6 mb-3">
                    <label for="confirmPassword" class="form-label">Confirm Password*</label>
                    <input 
                      type="password" 
                      class="form-control" 
                      id="confirmPassword" 
                      v-model="formData.confirmPassword" 
                      placeholder="Confirm your password"
                      required
                    >
                  </div>
                </div>
                
                <!-- Sponsor Fields -->
                <div v-if="isSponsor" class="mt-4">
                  <h4 class="mb-3">Sponsor Information</h4>
                  
                  <div class="row">
                    <div class="col-md-6 mb-3">
                      <label for="company_name" class="form-label">Company Name*</label>
                      <input 
                        type="text" 
                        class="form-control" 
                        id="company_name" 
                        v-model="formData.company_name" 
                        placeholder="Enter your company name"
                        required
                      >
                    </div>
                    
                    <div class="col-md-6 mb-3">
                      <label for="industry" class="form-label">Industry</label>
                      <select class="form-select" id="industry" v-model="formData.industry">
                        <option value="" disabled>Select an industry</option>
                        <option v-for="option in industryOptions" :key="option" :value="option">
                          {{ option }}
                        </option>
                      </select>
                    </div>
                  </div>
                  
                  <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i> Note: Sponsor accounts require approval before activation.
                  </div>
                </div>
                
                <!-- Influencer Fields -->
                <div v-if="isInfluencer" class="mt-4">
                  <h4 class="mb-3">Influencer Information</h4>
                  
                  <div class="row">
                    <div class="col-md-6 mb-3">
                      <label for="influencer_name" class="form-label">Influencer Name*</label>
                      <input 
                        type="text" 
                        class="form-control" 
                        id="influencer_name" 
                        v-model="formData.influencer_name" 
                        placeholder="Enter your influencer name"
                        required
                      >
                    </div>
                    
                    <div class="col-md-6 mb-3">
                      <label for="category" class="form-label">Category</label>
                      <select class="form-select" id="category" v-model="formData.category">
                        <option value="" disabled>Select your category</option>
                        <option v-for="option in categoryOptions" :key="option" :value="option">
                          {{ option }}
                        </option>
                      </select>
                    </div>
                  </div>
                  
                  <div class="row">
                    <div class="col-md-6 mb-3">
                      <label for="niche" class="form-label">Niche</label>
                      <input 
                        type="text" 
                        class="form-control" 
                        id="niche" 
                        v-model="formData.niche" 
                        placeholder="Describe your niche (e.g., Vegan Food, Tech Reviews)"
                      >
                    </div>
                    
                    <div class="col-md-6 mb-3">
                      <label for="reach" class="form-label">Reach (Followers)</label>
                      <input 
                        type="number" 
                        class="form-control" 
                        id="reach" 
                        v-model="formData.reach" 
                        placeholder="Your total follower count"
                      >
                    </div>
                  </div>
                </div>
                
                <div class="alert alert-danger mt-3" v-if="error">
                  {{ error }}
                </div>
                
                <div class="d-grid mt-4">
                  <button type="submit" class="btn btn-primary py-2" :disabled="loading">
                    <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
                    {{ loading ? 'Registering...' : 'Create Account' }}
                  </button>
                </div>
                
                <p class="text-center mt-3 mb-0">
                  Already have an account? 
                  <router-link to="/login" class="fw-bold text-decoration-none">Log In</router-link>
                </p>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template> 